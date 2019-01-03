# Flask-admin-with-TencentCos3
Use flask admin to management Tencent COS3 static files. python 2.7

Add it to your project and use it like this
```
# -*- coding: utf-8 -*-
from flask import Flask
from tencent import TencentFileAdmin

app = Flask(__name__)
admin = Admin(app)
admin.add_view(TencentFileAdmin())
```
