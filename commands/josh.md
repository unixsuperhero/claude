---
description: Review pull requests for architecture and design quality
---

run the following bash commands:

```sh
curdt=`date +%Y%m%d%H%M%S`
mkdir -pv ~/notes/slash-test
echo "testing: $ARGUMENTS" >~/notes/slash-test/tst.${curdt}
export >>~/notes/slash-test/tst.${curdt}
echo "SESSION ID: $CLAUDE_CODE_SESSION_ID" >>~/notes/slash-test/tst.${curdt}
echo "SESSION ID: $CLAUDE_CODE_SESSION_ID" >>~/notes/slash-test/tst.${curdt}.with_env
/usr/bin/env export >>~/notes/slash-test/tst.${curdt}.with_env
```

that's it
