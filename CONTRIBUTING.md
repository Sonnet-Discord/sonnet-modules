# Contributing Guidelines
- Modules will be submitted as /mod/\<username\>/\<modulename\>/\*
- Modules will include a README.md explaining:
  - What they do
  - Minimum sonnet version they require
- Modules will include bloat.json which documents:
  - Command names used (`"commands":[]`)
  - DB table names used (`"tables":[]`)
  - Sonnet config names used (`"configs":[]`)
  - Event names used (`"events":[]`)
  - Config caches used (`"caches":[]`)
## Example:
```bash
> ls GITROOT/mod/ultrabear/marketrep/
README.md bloat.json cmd_marketrep.py
```
GITROOT/mod/ultrabear/marketrep/README.md
```md
# Market Rep
This is a simple command module that implements tracking market rep of members
# Min sonnet version
- V1.2.3
```
GITROOT/mod/ultrabear/marketrep/bloat.json
```json
{
	"commands":["mr-add", "mr-remove", "mr-addrole"],
	"tables":["marketrep"],
	"configs":["mr-roles"],
	"caches":[],
}
```
Note: as no `events` are used by this module it omits writing the json key to an empty list, this holds true for all keys
