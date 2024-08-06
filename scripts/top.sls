base:
  10.8.11.171:
  - base.env_init
  - iptables.init
  - nginx.env_init
  - php.env_init


# cat /srv/salt/iptables/init.sls
###### 清空原规则 ######
clear_iptables:
  cmd.run:
  {% if grains['osfinger'] == 'CentOS-6' %}
    - name: service iptables stop && echo >/etc/sysconfig/iptables 
  {% elif grains['osfinger'] == 'CentOS Linux-7' %}
    - name: systemctl stop iptables && echo >/etc/sysconfig/iptables
  {% endif %}

#### 添加白名单ip
{% for fw, rule in pillar['white_ips'].iteritems() %}
{{ fw }}_INPUT:
  iptables.insert:
     - position: 1
     - table: filter
     - chain: INPUT
     - jump: ACCEPT
     - source: {{ rule['allowip'] }}
     - save: True

{{ fw }}_OUTPUT:
  iptables.insert:
     - position: 1
     - table: filter
     - chain: OUTPUT
     - jump: ACCEPT
     - destination: {{ rule['allowip'] }}
     - save: True
{% endfor %}

###### 获取自定义需要开放的服务端口并加入iptables规则中(同时取消状态追踪) ### 如果有对外开放的服务时 ###
{% if 'open_allow' in pillar.keys() %}
{% for eachfw, fw_rule in pillar['open_allow'].iteritems() %}
{{ eachfw }}_INPUT:
  iptables.append:
#     - position: 1 
     - table: filter
     - chain: INPUT
     - jump: ACCEPT
     - match: state
     - connstate: NEW,ESTABLISHED
     - protocol: {{ fw_rule['procto'] }} 
     - dport: {{ fw_rule['port'] }}
     - save: True

{{ eachfw }}_OUTPUT:
  iptables.append:
#     - position: 1 
     - table: filter
     - chain: OUTPUT
     - jump: ACCEPT
     - match: state
     - connstate: ESTABLISHED
     - sport: {{ fw_rule['port'] }}
     - protocol: {{ fw_rule['procto'] }}
     - save: True

{{ eachfw }}_NOTRACK_FROM_OUTPUT:
  iptables.insert:
     - position: 1 
     - table: raw
     - chain: OUTPUT
     - jump: NOTRACK
     - match: state
     - connstate: ESTABLISHED
     - sport: {{ fw_rule['port'] }}
     - protocol: {{ fw_rule['procto'] }}
     - save: True

{{ eachfw }}_NOTRACK_TO_OUTPUT:
  iptables.insert:
     - position: 1 
     - table: raw
     - chain: OUTPUT
     - jump: NOTRACK
     - match: state
     - connstate: ESTABLISHED
     - dport: {{ fw_rule['port'] }}
     - protocol: {{ fw_rule['procto'] }}
     - save: True

{{ eachfw }}_NOTRACK_FROM_PREROUTING:
  iptables.insert:
     - position: 1 
     - table: raw
     - chain: PREROUTING 
     - jump: NOTRACK 
     - match: state
     - connstate: ESTABLISHED
     - sport: {{ fw_rule['port'] }}
     - protocol: {{ fw_rule['procto'] }}
     - save: True

{{ eachfw }}_NOTRACK_TO_PREROUTING:
  iptables.insert:
     - position: 1 
     - table: raw
     - chain: PREROUTING 
     - jump: NOTRACK
     - match: state
     - connstate: ESTABLISHED
     - dport: {{ fw_rule['port'] }}
     - protocol: {{ fw_rule['procto'] }}
     - save: True
{% endfor %}
{% endif %}

# 允许访问外网服务
{% for fw, rule in pillar['out_allow'].iteritems() %}
{{ fw }}_INPUT:
  iptables.insert:
     - position: 1 
     - table: filter
     - chain: INPUT
     - jump: ACCEPT
     - match: state
     - connstate: ESTABLISHED
     - protocol: {{ rule['procto'] }} 
     - sport: {{ rule['port'] }}
     - save: True

{{ fw }}_OUTPUT:
  iptables.insert:
     - position: 1 
     - table: filter
     - chain: OUTPUT
     - jump: ACCEPT
     - match: state
     - connstate: NEW,RELATED,ESTABLISHED
     - protocol: {{ rule['procto'] }}
     - dport: {{ rule['port'] }}
     - save: True
{% endfor %}

# 允许ping出 
allow_ping_OUTPUT:
  iptables.append:
     - table: filter
     - chain: OUTPUT
     - jump: ACCEPT
     - match: state
     - connstate: NEW,RELATED,ESTABLISHED
     - protocol: icmp
     - comment: "Allow Ping OUT"
     - save: True

# 允许ping入
allow_icmp_INPUT:
  iptables.append:
     - table: filter
     - chain: INPUT
     - jump: ACCEPT
     - match: state
     - connstate: NEW,ESTABLISHED
     - protocol: icmp
     - comment: "Allow Ping IN"
     - save: True

# 设置INPUT默认策略为DROP 
default_to_INPUT:
  iptables.set_policy:
    - chain: INPUT
    - policy: DROP
    - save: True
 
# 设置OUTPUT默认策略为DROP
default_to_OUTPUT:
  iptables.set_policy:
    - chain: OUTPUT
    - policy: DROP
    - save: True

# 设置FORWARD默认策略为DROP
default_to_FORWARD:
  iptables.set_policy:
    - chain: FORWARD 
    - policy: DROP
    - save: True

###### 重启iptables 并保持开机自动加载 ######
iptables-service:
  service.running:
    - name: iptables 
    - reload: True
    - enable: True
