from utils import *

with open("config.yml") as f:
  config = yaml.load(f)
inst_type = config["inst_type"]
sys_op = config["sys_op"]
PEM = config["PEM"]
KEY = config["KEY"]
REGION = config["REGION"]
REGION_SPEC = config["REGION_SPEC"]
AWSUSER = config["AWSUSER"]
VPDID = config["VPDID"]
SUBNETID = config["SUBNETID"]
EC2GROUP = config["EC2GROUP"]
ami = config["AMI"]
on_demand_url = config["on_demand_url"]
mount_to = config["mount_to"]
inst_mech = config["inst_mech"]
username = config["username"]

running_ins, running_type, running_ip, stopped_ins, stopped_type, pending_ins, pending_type = get_ondemand_info(KEY)

request_ids, instance_ids, request_states, instance_types, request_types = get_spot_info(KEY)

mount_dir0 = os.path.expanduser('~')+"/ec2/"
if not os.path.exists(mount_dir0):
    os.makedirs(mount_dir0)
mount_dir = mount_dir0
if not os.path.isdir(mount_dir) or not os.listdir(mount_dir):
    mount_dir = ""

print("### running instances: ###")
print("id: "+str(running_ins))
print("type: "+str(running_type))
print("ip: "+str(running_ip))
print("### stopped instances: ###")
print("id: "+str(stopped_ins))
print("type: "+str(stopped_type))
print("### pending instances: ###")
print("id: "+str(pending_ins))
print("type: "+str(pending_type))
print("### spot instance request info: ###")
print("request_ids: "+str(request_ids))
print("instance_ids: "+str(instance_ids))
print("request_states: "+str(request_states))
print("instance_types: "+str(instance_types))
print("request_types: "+str(request_types))

#print("### mounted directory: ###")
#print(mount_dir)
print("----------------")


choices = "\n".join([\
    "0: launch an instance",\
    "1: start an instance",\
    "2: stop an instance",\
    "3: terminate an instance",\
    "4: mount an instance",\
    "5: unmount an instance",\
    "6: forward traffice from a remote port to a local port",\
    "7: ssh to an instance",\
    "8: cancel a spot instance request",\
    "9: exit",\
    "select a task: "])
choice = input(choices)
print("task: "+choice)
while choice not in [str(i) for i in range(len(choices)-1)]:
    print("task \""+choice+"\" not supported.")
    print("----------------")
    choice = input(choices)
    print("task: "+choice)
print("----------------")


### 0. launch an instance
if choice == "0":
  choice2 = print_options(inst_type, "which instance type to launch: ") 
  INST=inst_type[int(choice2)]
  AMI=ami["gpu"] if "p2" in INST else ami["cpu"]
  choice3 = print_options(inst_mech, "on demand or spot instance: ")

  # on demand
  if choice3 == "0":
    # if one wants the ec2 server to execute a script upon launching, use --user-data flag below
    sp.run(["aws", "ec2", "run-instances", "--image-id", AMI, "--count", "1", "--instance-type", INST, "--associate-public-ip-address", "--key-name", KEY, "--security-group-ids", EC2GROUP, "--subnet-id", SUBNETID, "--profile", AWSUSER, "--region", REGION])
  # spot
  elif choice3 == "1":
    on_demand_price = get_instance_price(on_demand_url, sys_op, REGION, INST)
    price_list = ["on demand price: "+on_demand_price, "another price"]
    choice4 = print_options(price_list, "choose a price at which to bid for the spot instance: ")
    if choice4 == "0":
        price = on_demand_price
    elif choice4 == "1":
        price = float(input("enter a custom price: "))

    spot_spec = {"ImageId":AMI, "KeyName":KEY, "SecurityGroupIds":[EC2GROUP], "InstanceType":INST, "SubnetId":SUBNETID, "Placement":{"AvailabilityZone":REGION_SPEC}}
    with open("specification.json", "w") as fw:
      json.dump(spot_spec, fw)

    _request_types = ["one-time", "persistent"]
    choice4 = print_options(_request_types, "one-time or persistent spot instance request: ")
    sp.run(["aws", "ec2", "request-spot-instances", "--spot-price", str(price), "--instance-count", "1", "--type", _request_types[int(choice4)], "--launch-specification", "file://specification.json"])

### 1. start an instance
elif choice == "1" and len(stopped_ins) != 0:
    choice2 = print_options(stopped_ins, "which instance to start: ", stopped_type)
    sp.run(["aws", "ec2", "start-instances", "--instance-ids", stopped_ins[int(choice2)]])

    while running_ip == []:
        _, _, running_ip, _, _, _, _ = get_ondemand_info(KEY)
    
    #sp.run(["sudo", "scp", "-i", "anglimoses.pem", "init.sh", "ec2-user@"+running_ip[int(choice2)]+":/home/ec2-user/.bashrc_temp"])

    print("instance started.")

### 2. stop an instance
elif choice == "2" and len(running_ins) != 0:
    choice2 = print_options(running_ins, "which instance to stop: ", running_type)
    sp.run(["aws", "ec2", "stop-instances", "--instance-ids", running_ins[int(choice2)]])

### 3. terminate an instance
elif choice == "3" and (len(running_ins) != 0 or len(stopped_ins) != 0): 
    ctr = 0
    for ins in running_ins:
        print(str(ctr)+": "+ins+", "+running_type[ctr])
        ctr += 1
    for ins in stopped_ins:
        print(str(ctr)+": "+ins+", "+stopped_type[ctr-len(running_ins)])
        ctr += 1
    choice2 = input("which instance to terminate: ")
    while choice2 not in [str(i) for i in range(len(running_ins)+len(stopped_ins))]:
        choice2 = input("which instance to terminate: ")
    sp.run(["aws", "ec2", "terminate-instances", "--instance-ids", running_ins[int(choice2)] if int(choice2)<len(running_ins) else stopped_ins[int(choice2)-len(running_ins)]])

### 4. mount an instance
elif choice == "4" and len(running_ip) != 0:
    if mount_dir != "":
        print(mount_dir+" is already mounted.")
    else:
        #cmd = ["sudo", "sshfs", "ec2-user@"+running_ip[0]+":"+mount_to, mount_dir0, "-o", "IdentityFile="+os.getcwd()+"/anglimoses.pem"]
        cmd += ["-o", "allow_other,default_permissions", "-o", "workaround=rename", "-o", "uid="+uid]
        print(" ".join(cmd))
        sp.run(cmd)

### 5. unmount an instance
elif choice == "5" and mount_dir != "":
    sp.run(["sudo", "umount", mount_dir])

### 6. direct traffic from a remote port to a local port (for jupyter, tensorboard, etc.)
elif choice == "6":
    choice2 = print_options(running_ins, "which instance to ssh to: ", running_type)
    port_remote = input("remote port (e.g., 8888, 6006): ")
    port_local = input("local port (e.g., 8889, 16006): ")
    sp.run(["sudo", "ssh", "-i", "anglimoses.pem", "-f", "ec2-user@"+running_ip[int(choice2)], "-L", port_local+":127.0.0.1:"+port_remote, "-N"])#, "&>", "/dev/null"])

### 7. ssh to an instance
elif choice == "7" and len(running_ip) != 0:
    choice2 = print_options(running_ins, "which instance to ssh to: ", running_type)
    sp.run(["sudo", "scp", "-i", "anglimoses.pem", "init_bash", username+"@"+running_ip[int(choice2)]+":/home/"+username+"/.bashrc_temp"])
    sp.run(["sudo", "scp", "-i", "anglimoses.pem", "init_vim", username+"@"+running_ip[int(choice2)]+":/home/"+username+"/.vimrc"])
    
    #sp.run(["sudo", "ssh", "-t", "-i", "anglimoses.pem", username+"@"+running_ip[int(choice2)]])
    # bypass ~/.bashrc and use the custom ~/.bashrc_temp
    sp.run(["sudo", "ssh", "-t", "-i", "anglimoses.pem", username+"@"+running_ip[int(choice2)], "bash --rcfile /home/"+username+"/.bashrc_temp ; rm /home/"+username+"/.bashrc_temp"])

### 8. cancel a spot instance request (something that has to be done before terminating a persistent spot intance)
elif choice == "8":
  # interpretation of the output: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-bid-status.html
  # example: http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-spot-instance-requests.html
  # spot instance pricing: https://aws.amazon.com/ec2/spot/pricing/
  uncancelled_request_ids = []
  for i in range(len(request_states)):  
    if request_states[i] != "cancelled":
      uncancelled_request_ids.append(str(request_ids[i]))
  choice2 = print_options(uncancelled_request_ids, "which spot instance request to cancel: ")
  sp.run(["aws", "ec2", "cancel-spot-instance-requests", "--spot-instance-request-ids", uncancelled_request_ids[int(choice2)]])

### 10. exit
else:
    if choice != "9":
        print("task not supported in this case")
    sys.exit(0) 

