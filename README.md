# Flask-admin-with-TencentCos3
Use flask admin to management Tencent COS3 static files. python 2.7

**requirements**
```
flask>= 1.0.2
flask-admin>=1.5.2
flask-security>=3.0.0
cos-python-sdk-v5
```

Add it to your project and use it like this
```
# -*- coding: utf-8 -*-
from flask import Flask
from tencent import TencentFileAdmin

app = Flask(__name__)
admin = Admin(app)
admin.add_view(TencentFileAdmin())
```
