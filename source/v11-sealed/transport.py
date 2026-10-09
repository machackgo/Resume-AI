"""Task-local SSH connection reuse; authentication and host-key checks unchanged."""
import json,tempfile
from pathlib import Path
D=Path(__file__).resolve().parent
p=D/'ssh-transport.json'
if p.exists():control=Path(json.loads(p.read_text())['control_path'])
else:
 control=Path(tempfile.mkdtemp(prefix='resume-semantic-ssh-'))/'connection'
 p.write_text(json.dumps(dict(control_path=str(control)),indent=2))
control.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
SSH_OPTIONS=['-o','BatchMode=yes','-o','ConnectTimeout=10','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','-o','ControlMaster=auto','-o','ControlPersist=600','-o','ControlPath='+str(control)]
