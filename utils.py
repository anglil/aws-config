import os
import sys 
import json
import subprocess as sp

from bs4 import BeautifulSoup
import requests
import json
import yaml
import re
import ast


def print_options(options, msg, options2=None):
  ctr = 0
  for option in options:
    if options2 == None:
      print(str(ctr)+": "+option)
    else:
      print(str(ctr)+": "+option+", "+options2[ctr])
    ctr += 1
  choice = input(msg)
  while choice not in [str(i) for i in range(len(options))]:
    choice = input(msg)
  return choice


def get_instance_price(url, sys_os, region, inst_type):
  #def comment_remover(text):
  #  def replacer(match):
  #    s = match.group(0)
  #    if s.startswith('/'):
  #      return " " # note: a space and not an empty string
  #    else:
  #      return s
  #  pattern = re.compile(
  #    r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
  #    re.DOTALL | re.MULTILINE
  #    )
  #  return re.sub(pattern, replacer, text)
  
  page = requests.get(url)
  html = page.content
  parsed_html = BeautifulSoup(html, "lxml")
  data_models = parsed_html.findAll("div", attrs={"data-model":True})
  
  js_url = ""
  for data_model in data_models:
    js = data_model["data-model"]
    if sys_os in js.lower():
      js_url = js
      break
  
  if js_url == "":
    raise ValueError("couldn't find the js.")
  
  try:
    js_content = requests.get("http:"+js_url).text
  except:
    raise ValueError("invalid url: http:"+js_url)
  js_content = js_content[js_content.index("(")+1: js_content.rindex(")")]
  
  js_wo_quotation = "js_wo_quotation"
  with open(js_wo_quotation, "w") as fw:
    fw.write(js_content)
  
  sp.check_call(["node", "add_quotation.js"])
  
  js_w_quotation = "js_w_quotation"
  with open(js_w_quotation) as f:
    js_content = json.load(f)
  
  price = ""
  regions = js_content["config"]["regions"]
  for item in regions:
    if item["region"] == region:
      for vol in item["instanceTypes"]:
        for ins in vol["sizes"]:
          if ins['size'] == inst_type:
            price = ins["valueColumns"][0]["prices"]["USD"]
            break
  return price


def get_ondemand_info(KEY):
  aws_info = sp.run(["aws", "ec2", "describe-instances"], stdout=sp.PIPE).stdout.decode('utf-8')
  instances = json.loads(aws_info)

  running_ins = []
  running_type = []
  running_ip = []
  stopped_ins = []
  stopped_type = []
  pending_ins = []
  pending_type = []

  if "Reservations" in instances:
    instances = instances["Reservations"]
      
    #auid = str(sp.run(["id"], stdout=sp.PIPE).stdout, 'utf-8').split(' ')[0].split('=')[1].split('(')[0]
    #gid = str(sp.run(["id"], stdout=sp.PIPE).stdout, 'utf-8').split(' ')[1].split('=')[1].split('(')[0]
      
          
    for item in instances:
      for ins in item["Instances"]:
        if "KeyName" in ins and ins["KeyName"] == KEY:
          iid = ins["InstanceId"]
          tp = ins["InstanceType"]
          status = ins["State"]["Name"]
          if status == "stopped":
            stopped_ins.append(iid)
            stopped_type.append(tp)
          elif status == "running":
            running_ins.append(iid)
            running_type.append(tp)
            ip = ins["PublicIpAddress"]
            running_ip.append(ip)
          else:
            pending_type.append(tp)
            pending_ins.append(iid)
  return running_ins, running_type, running_ip, stopped_ins, stopped_type, pending_ins, pending_type

def get_spot_info(KEY):
  aws_info = sp.run(["aws", "ec2", "describe-spot-instance-requests"], stdout=sp.PIPE).stdout.decode('utf-8')
  requests = json.loads(aws_info)

  request_ids = []
  instance_ids = []
  request_states = []
  instance_types = [] # one-time or persistent
  request_types = []

  if 'SpotInstanceRequests' in requests:
    requests = requests['SpotInstanceRequests']
    for request in requests:
      if "KeyName" in request["LaunchSpecification"] and request["LaunchSpecification"]["KeyName"] == KEY:
        request_ids.append(request["SpotInstanceRequestId"])
        if "InstanceId" in request:
            instance_ids.append(request["InstanceId"])
        request_states.append(request["State"])
        instance_types.append(request["LaunchSpecification"]["InstanceType"])
        request_types.append(request["Type"])
  
  return request_ids, instance_ids, request_states, instance_types, request_types







