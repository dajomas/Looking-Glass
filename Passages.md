* Doors
  * 2 way pass through
  * Single Click to pass through
* Locked/Unlocked Doors
  * Appear as door on viewer page
  * Appears as locked on admin page
  * 2 way pass through when Unlocked
  * Can start either Locked or Unlocked
  * Double click to toggle on admin page only
  * Single click on Locked door in viewer shows it as locked
  * Single click to pass through when Unlocked
* Secret Door
  * Does not show on viewer page if not yet discovered
  * Double click in admin page when discovered
  * When discovered, can become either a Door or a Locked/Unlocked Door
* Portals
  * Always a pair -> 2 wall elements
  * Each side of each portal element can be either:
    * Entry (Arrow points to portal)
    * Exit (Arrow points away from portal)
    * Both (Double arrow pointing towards and away from portal)
    * None
  * There must always be at least 1 Entry and 1 Exit
  * Every Entry MUST have exactly 1 Exit
  * There can not be an Exit without an Entry
* Locked/Unlocked Portal
  * Acts the same as a Locked/Unlocked Door
  * When Unlocked becomes a Portal
* Secret Portal
  * Acts the same as a Secret Door
  * When discovered, can become either a Portal or a Locked/Unlocked Portal

Colors
|Entity|Color|Wall Dashed|Arrow in Admin Screen|Arrow in Viewer Screen|Click Action in Admin Screen|Click Action in Viewer Screen|Double Click Action|Note|
|---|---|---|---|---|---|---|---|---|
|Door|Blue|No|Yes|Yes|Uncover area behind the door|Uncover area behind the door|-|
|Locked Door|Orange|Yes|Yes|Show as Door|-|Show arrow as Locked Door|Unlock Door|
|Unlocked Door|Orange|No|Yes|Show as Door|Uncover area behind the door|Uncover area behind the door|Lock Door|
|Secret Door|Purple|Yes|Yes|No|-|-|Become Door, Locked Door or Unlocked Door|Arrow does not disappear
|Portal Entry|Silver|No|Yes|Yes|Uncover area behind paired portal exit|Uncover area behind paired portal exit|-|Arrow does not disappear
|Portal Exit|Silver|No|Yes|No|-|-|-|Arrow does not disappear
|Portal 2-way|Silver|No|Yes|Yes|Uncover area behind paired exit|Uncover area behind paired exit|-|Arrow does not disappear
|Locked Portal Entry|Brown|Yes|