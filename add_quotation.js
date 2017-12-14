var fs = require("fs");
var js_wo_quotation = "js_wo_quotation";
var text = fs.readFileSync(js_wo_quotation, "utf-8");
text = text.replace(/(['"])?([a-zA-Z0-9_]+)(['"])?:([^\/])/g, '"$2":$4');
//console.log(text);
var js_w_quotation = "js_w_quotation";
fs.writeFile(js_w_quotation, text, function(err) {
  if(err) {
    return console.log(err);
  }
});
