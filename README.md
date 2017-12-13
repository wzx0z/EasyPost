运行环境准备：
1. 安装Python2.7版本。
2. 若存在多个版本Python或安装Python时未勾选将Python添加到环境变量，请检查系统环境变量Path是否配置Python和Python\Scripts路径。
3. 在cmd下输入pip install requests-2.18.4-py2.py3-none-any.whl安装requests库。
4. 在cmd下输入pip install xlrd-1.1.0-py2.py3-none-any.whl安装xlrd库。
5. 解压PyYAML，在cmd下输入python setup.py install安装PyYAML库
6. 在cmd下输入python进入python shell，分别输入import requests、import xlrd、import yaml，若没有报错则运行环境准备完成。

如何获取操作模板：
1. 在apic gui上进行相关操作对象
2. 在对象上右键，Save as...，选择Only Configuration、Subtree、json
3. 对需要自定义的数据使用%{xxx}s替换
4. 请留意对象的status状态信息，对象状态会导致不同的操作（Created、Modified、Deleted...）

如何编写playbooks：
1. 每个playbooks可以包含多个job，每个job以‘- job:’开头，属性：description（工作描述）、tasklist（任务列表）
2. 每个tasklist可以包含多个task，每个以‘- task:’开头，属性：description（任务描述）、template（模板路径）、sourcedata（数据路径）

操作步骤：
1. credentials.py中填写用于apic登陆的相关信息。
2. 在template.json中填写需要post的json模板数据，其中自定义数据用 %{xxx}s 代替，xxx为自定义名称。
3. 在data.xlsx中填写批量操作的自定义数据，第一行表头即template.json中自定义数据的xxx自定义名称。
4. 在playbooks.yaml中编排批量操作
4. python Common.py -p <playbooks>将会根据playbooks将data.xlsx中的数据逐行应用到template.json模板上并post请求到apic。

注意：
1. 脚本默认忽略https不安全的警告，若需要提示或使用认证，请修改脚本。详情见requests库的guide。
2. api默认为/api/mo/uni.json，使用其他api请在data.xlsx中添加一列表头为api_url的数据列（url不用包含apic地址，使用默认api则可以不填）。
3. 脚本的执行过程遇到错误就会停止运行，apic会提示可能的出错信息，请注意输出的错误信息。返回response 200即为post成功。
4. 建议先使用脚本post一条配置，确保配置推送正确后再批量。