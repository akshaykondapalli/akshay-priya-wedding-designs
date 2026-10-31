import json
d=json.load(open('/home/claude/tools/editorial/motifs.json'))
t=open('/home/claude/tools/editorial/index.template.html').read()
t=t.replace('{{MUGGU}}',d['muggu']).replace('{{THORANAM}}',d['thoranam'])
open('/home/claude/site/editorial/index.html','w').write(t)
print('built', len(t))
