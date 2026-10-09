with open('yonetim/templates/yonetim/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

import re
content = re.sub(r'<<<<<<< HEAD.*?EfeZade<span>Group</span>\n=======\n.*?EfeZade<span>Group</span>\n>>>>>>> .*?\n', '                EfeZade<span>Group</span>\n', content, flags=re.DOTALL)
# wait let's just make it simpler:
content = re.sub(r'<<<<<<< HEAD\n.*?Efezade<span>Group</span>\n=======\n.*?EfeZade<span>Group</span>\n>>>>>>> [^\n]*\n', '                EfeZade<span>Group</span>\n', content, flags=re.DOTALL)

with open('yonetim/templates/yonetim/base.html', 'w', encoding='utf-8') as f:
    f.write(content)
