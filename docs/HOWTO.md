# How to...

## Create a new rule template for the security dashboard.

1. Choose a destination folder for your rules. For this demo we will use:
   1. `/opt/samapper/myrules`
1. Configure sam to look in your rule folder
   1. `export SAM__SECURITY__RULE_FOLDER=/opt/samapper/myrules`
1. Create your rule: See next paragraph.

Rule Templates are yml files, and require specific keywords to be defined.  Each rule must include the keys in the example below, although most can be left blank:

```yaml
# name: Required. quotes are optional unless you use yaml symbols
#       in the name.
name: My Rule Name

# type: Required. Either "immediate" or "periodic". Immediate
#       rules apply to individual traffic items, periodic rules
#       are applied against 5-minute time chunks.
type: immediate

# include: Optional.  Any external data sources you wish to use
#          in this rule.  Each list item is indented,
#          and consists of a name and a path.
include:
    name: /path/to/file.txt
    bad_hosts: ./bad_host_list.txt

# expose: Optional. Any in-app customization you would like to make
#         available to the user.  Each list item has multiple parts
#         to define what data to expect and how to present it to
#         the user.  Types supported include "text", "checkbox" and
#         "dropdown".  See inline comments below for more details.
expose:
    MyTextVariable:
        # label: Required. Descriptive text to explain what this
        #        variable is for.
        label: Destination address to watch

        # format: Required. One of "text", "dropdown", "checkbox".
        format: text

        # default: Required. Use this value if the user hasn't
        #          chosen one for themselves.
        default: "192.168.1.1"

        # regex: Optional. Use this rule to decide if user input is
        #        accepted or not.
        regex: "^192\\.168\\.1\\.[0-3]?[0-9]$"

    MyCheckbox:
        # label: Required. Descriptive text to explain what this
        #        variable is for.
        label: Use threshold

        # format: Required. One of "text", "dropdown", "checkbox".
        format: checkbox

        # default: Required. Use this value if the user hasn't
        #          chosen one for themselves. a blank checkbox
        #          is false, a checked checkbox is true.
        default: false

    MyDropdown:
        # label: Required. Descriptive text to explain what this
        #        variable is for.
        label: Protocol to watch

        # format: Required. One of "text", "dropdown", "checkbox".
        format: dropdown

        # default: Required. Use this value if the user hasn't
        #          chosen one for themselves. Should be one of
        #          the possible options below.
        default: "'TCP'"

        # options: Required. The dropdown list will present this
        #          list of options to the user, so that the user
        #          can pick one of them.
        options:
          - "'TCP'"
          - "'UDP'"
          - "'TCP' OR 'UDP'"

# actions: Optional. Actions are a way to override the default
#          reporting when the rule is triggered. User edits take
#          priority over these defaults. See inline comments
#          below for details on each option.
actions:
  # true or false. Enable alerts on broken rules
  alert_active: true

  # 1-8. Higher numbers mean greater severity.
  alert_severity: 8

  # text. The label to attach to the alert
  alert_label: Special Label

  # true or false. Enable emails sent when a rule is broken.
  email_active: true

  # text. The email address to send an alert to.
  email_address: abc@zyx.com

  # text. The subject of the alert.
  email_subject: "[SAM] Special Email Subject"

  # true or false. Send a SMS message on a broken rule.
  sms_active: true

  # text. Send the sms message to this number.
  sms_number: 1 123 456 7890

  # text. Content of the message to send.
  sms_message: "[SAM] Special SMS Message"

# subject: Required. Indicates which end of the connection to
#          report on. Must be 'src' or 'dst'. Usually src.
subject: src

# when: Required. This is the rule to evaluate.
#
# For immediate rules, you can specify src host, dst host, port,
# and protocol.  They can be combined with 'and' and/or 'or',
# negated with 'not', and can take lists. ports can also be
# specified with comparators.
#
# ex1.  src host 192.168.1.1 and dst host 192.168.1.2 and port 3306 and protocol TCP
#       trigger when 192.168.1.1 connects to 192.168.1.2 on port
#       3306 using TCP.
# ex2.  (src host 192.168.1.1 or dst host 192.168.1.2) and not port 3306 and protocol TCP
#       trigger when protocol is TCP, port isn't 3306, and either
#       src is 192.168.1.1 or dest is 192.168.1.2
# ex3.  port > 1024 and port < 1536
#       trigger when port is between 1024 and 1536 exclusive.
# ex4.  port in (80, 443, 8080)
#       trigger when port any of the three values.
# For periodic rules, you can specify any, all, or none of the above
# and an additional `having` clause.  In the having clause you can
# specify:
#     conn[links]  (total number of connections formed)
#     conn[ports]  (number of destination ports used)
#     conn[protocol]  (number of protocols used)
#     dst[hosts] (if subject=src only; number of distinct hosts contacted)
#     src[hosts] (if subject=dst only; number of distinct hosts contacted)
#
# ex1. having conn[links] > 1000
#      trigger when the number of connections involving the
#      subject (above) is greater than 1000 over a 5 minute period.
# ex2. src host 192.168.1.1 having conn[ports] > 300
#      trigger when 192.168.1.1 has connected to other hosts on more
#      than 300 distinct ports during a 5 minute period.
# ex3. protocol UDP having dst[hosts] = 8 and conn[links] > 100
#      trigger when the src formed more than 100 UDP connections to
#      exactly 8 distinct hosts over a 5 minute period.
when: src host 192.168.1.1 and dst host 192.168.1.2 and dst port 3306

```

Exposed parameters are applied by using replacement strings in the 'actions' and the 'when'.
In the following example, exposed parameters are used in the alert and condition.

```yaml
name: Network Scanning
type: periodic
include:
expose:
  threshold:
    label: This rule will trigger on a host if that host is connecting to more than this number of distinct other hosts over 5 minutes.
    format: text
    default: 600
    regex: "^\\d+$"
actions:
    email_active: true
    email_subject: "[SAM] Rule $rule_name triggered."
subject: src
when: having dst[hosts] > $threshold
```

The condition `having dst[hosts] > $threshold` is expanded into `having dst[hosts] > 600`

If the rule were triggered, an email would be sent with the given subject `[SAM] Rule $rule_name triggered` expanded into something like `[SAM] Rule MyRule triggered`.

The available variables are:
  - all exposed parameters
  - all included data
  - "rule_name" The name of the rule (not the name of the rule template)
  - "rule_desc" The description of the rule

Another sample, using a dropdown to specify protocol:
```yaml
name: Demo Rule
type: immediate
expose:
  proto:
    label: protocol to test
    format: dropdown
    default: udp, tcp
    options:
      - tcp
      - udp
      - udp, tcp
subject: src
when: protocol $proto
```

When executed, the condition is expanded into `WHERE protocol IN ('UDP', 'TCP')`

## Test a rule template
A rule template can be tested with the launcher using the "template" target.  This should provide enough information to make sure a template is ready for use.

```bash
python sam/launcher.py --target=template sam/rule_templates/netscan.yml
```

