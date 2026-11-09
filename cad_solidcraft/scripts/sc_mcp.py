"""Sequential stdio MCP client; one persistent design session per context."""
import json,os,subprocess,queue,threading,shutil
from pathlib import Path
class Client:
 def __init__(self,root,timeout=180):
  self.root=Path(root);self.timeout=timeout;self.seq=0;self.q=queue.Queue()
  cli=os.environ.get('SOLIDCRAFT_CLI') or shutil.which('solidcraft-cli')
  if not cli:raise RuntimeError('Set SOLIDCRAFT_CLI or install solidcraft-cli on PATH')
  mode=['--connect',os.environ['SOLIDCRAFT_CONNECT']] if os.environ.get('SOLIDCRAFT_CONNECT') else (['--headless'] if os.environ.get('SOLIDCRAFT_HEADLESS') == '1' else [])
  self.p=subprocess.Popen([cli,'mcp',*mode,'--allow-path',str(self.root),'--allow-path','/tmp'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
  def reader():
   for line in self.p.stdout:self.q.put(line)
   self.q.put(None)
  threading.Thread(target=reader,daemon=True).start()
  self.rpc('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'r3-cad','version':'1'}})
  self.send({'jsonrpc':'2.0','method':'notifications/initialized'})
 def send(self,v):self.p.stdin.write(json.dumps(v,ensure_ascii=False)+'\n');self.p.stdin.flush()
 def rpc(self,method,params):
  self.seq+=1;self.send({'jsonrpc':'2.0','id':self.seq,'method':method,'params':params})
  while True:
   s=self.q.get(timeout=self.timeout)
   if s is None:raise RuntimeError('SolidCraft exited')
   r=json.loads(s)
   if r.get('id')==self.seq:
    if 'error' in r:raise RuntimeError(r['error'])
    return r['result']
 def call(self,name,args=None):
  r=self.rpc('tools/call',{'name':name,'arguments':args or {}})
  if r.get('isError'):raise RuntimeError(r)
  for c in r.get('content',[]):
   if c.get('type')=='text':
    try:return json.loads(c['text'])
    except ValueError:pass
  return r
 def execute(self,command,**params):return self.call('execute',{'command':command,'params':params})
 def __enter__(self):return self
 def __exit__(self,*a):
  self.p.stdin.close()
  try:self.p.wait(timeout=5)
  except subprocess.TimeoutExpired:self.p.terminate();self.p.wait(timeout=5)
