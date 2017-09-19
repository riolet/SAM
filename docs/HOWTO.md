#How to...

##Create a new rule template for the security dashboard. 

1. Choose a destination folder for your rules. For this demo we will use:
   1. `/opt/samapper/myrules`
1. Configure sam to look in your rule folder
   1. `export SAM__SECURITY__RULE_FOLDER=/opt/samapper/myrules`
1. Create your rule: See next paragraph.

Rule Templates are yml files, and require specific keywords to be defined.  Each rule must include the keys in the example below, although most can be left blank:

```yaml
# This is a comment
---  # Optional. beginning of yaml definition.
name: "my rule name" # Required. quotes are optional unless you use yaml symbols in the name.
```

