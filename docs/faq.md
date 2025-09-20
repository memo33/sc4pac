# Troubleshooting & FAQs

*All the answers to common problems and questions.*

## Application doesn't start :id=app-not-starting

The application should display a detailed message explaining the problem and how to resolve it.

- On **Windows**:
  - One common problem is that the Java version on your system is too old, typically Java version 8, so you need to install a newer Java. Reboot your system afterwards.
  - Sometimes, trying the web-app version as alternative can help.

- On **macOS**:
  - The system's security settings block the first launch of the application:
    - Open the *Finder* and control-click the application to open it.
    - If the problem persists, go to *System Preferences* → *Security & Privacy* → *General* and click the padlock icon, then *Open Anyway*.
      All of the following files may be affected by the blocking: `launch-GUI-web-macOS.command`, `cli/sc4pac`, `cli/sc4pac-cli.jar`, `cli/cicdec/cicdec.exe`.

If there's no error message at all, please report the problem.
(If you know how, also try launching the **sc4pac-gui** from the command-line to check for potential errors there.)

## Antivirus warnings :id=antivirus-warnings

Some Antivirus Software may falsely flag the application as a virus.
- To be absolutely sure the files on your system are in fact correct, you can
  [verify the checksum](https://howardsimpson.blogspot.com/2022/01/quickly-create-checksum-in-windows.html)
  of the downloaded ZIP file against the [checksums published on Github](https://github.com/memo33/sc4pac-gui/releases).
- If the checksum matches, the file is identical to the original upload, and you can unblock the application in your Antivirus Software.

## Which Plugins folder to use? :id=which-plugins-folder

The game looks for Plugins in two different locations:
1. `Documents\SimCity 4\Plugins`
2. `Program Files\Maxis\SimCity 4\Plugins` (or equivalent)

The exact location depends on the edition of your game and on your operating system.

For *sc4pac*, it is recommended to choose the location under `Documents`, mainly to avoid file permission problems, but either option works.

## Plugins don't appear in the game :id=plugins-not-loading

When creating a Profile, make sure the Plugins folder location you choose is the correct one.
*Sc4pac* does not attempt to pick up the actual location used by the game, but only provides the most common one as default:
`C:\Users\<username>\Documents\SimCity 4\Plugins`.
Depending on the edition of your game, a different location may be needed.

## The game doesn't start :id=game-not-starting

Not an *sc4pac* issue, but make sure your game is properly configured and runs smoothly before installing heaps of plugins, as it will make troubleshooting your problem easier.

## DLL files not working :id=dlls-not-loading

1. DLLs must be installed in the _root_ of your Plugins folder, not a subfolder.
   For this to work, the Plugins folder location in your **![](_speed.svg)Dashboard** must point to the actual `Plugins` folder, not a subfolder.

2. Some DLLs come with `.ini` configuration files.
   To complete the installation of such a DLL, remember to copy the `.ini` file from the package subfolder inside your Plugins to the root of your Plugins folder.

   <details>
   <summary>Detailed example</summary>

   - For the package `pkg=null-45:query-tool-ui-extensions-dll` for example,<br>
     copy `Plugins\150-mods\null-45.query-tool-ui-extensions-dll.2.5.0-1.sc4pac\SC4QueryUIHooks.ini`<br>
     to `Plugins\SC4QueryUIHooks.ini`.
   - Then, edit the new file to set your preferences.
   - Repeat this whenever the DLL is updated to a newer version.

   </details>

3. Many DLLs write a `.log` file to the root of your Plugins folder. Check it for potential errors.
   If the `.log` file is missing, chances are the DLL failed to load, for example due to a missing *VC x86 Redistributable*.

4. If you have manually installed DLLs into the other Plugins folder, make sure the same DLL doesn't exist in both Plugins folders.

5. DLLs don't work with the **macOS** edition of the game.

## Manually installed Plugins aren't picked up by sc4pac :id=manual-plugins-vs-sc4pac

That's how it is.
Even if you place your pre-existing plugins in folders such as `075-my-plugins`, *sc4pac* doesn't touch these in any way.
They are managed by you alone.

## Changing the Plugins folder location :id=changing-plugins-location

1. The Plugins folder location of an existing *sc4pac* Profile can only be changed manually by

   <details>
   <summary>editing a configuration file.</summary>

   - Go to **![](_settings.svg)Settings** → *Profiles configuration folder* and open the folder.
   - The folder contains a subfolder for each Profile. Open the file `sc4pac-plugins.json` of your Profile in a text editor and edit the `pluginsRoot` attribute.
   - Move the Plugins folder to the new location.
   - Restart *sc4pac*.

   </details>

2. The location in which the game looks for the Plugins folder can be changed by launching the game with the
   `-UserDir:"..."` [launch parameter](https://www.wiki.sc4devotion.com/index.php?title=Shortcut_Parameters#User_Dir).

## Renaming/deleting a Profile :id=renaming-deleting-profile

Currently, this can only be done by manually

<details>
<summary>editing a configuration file.</summary>

- Go to **![](_settings.svg)Settings** → *Profiles configuration folder* and open the folder.
- Open the file `sc4pac-profiles.json` in a text editor and edit it.
- Restart *sc4pac*.

</details>

## Uninstalling a package doesn't work :id=unstarring-not-working

Unstarring![](_unstar.svg) a package `a:b` has no effect if it's required by another installed package `c:d`.
Uninstalling `a:b` alone would mean that `c:d` is missing a dependency, so that's not allowed.
To uninstall `a:b`, make sure to unstar![](_unstar.svg) `c:d`, too, as well as any other packages that depend on `a:b` (or `c:d`).

## Re-installing a single package :id=reinstalling-package

Sometimes, you may want to re-install a package, for example if you accidentally deleted one of its files from your Plugins.
The usual approach is:
- Unstar![](_unstar.svg) the package, then *![](_refresh.svg)Update All* to uninstall it.
- Star![](_star.svg) the package again, then *![](_refresh.svg)Update All* to install it again.

However, unstarring![](_unstar.svg) has no effect if other installed packages depend on it.
In such cases, either uninstall the packages depending on it, as well.
Or, alternatively, a re-install of a single package can be triggered by manually

<details>
<summary>editing a configuration file.</summary>

- Go to **![](_settings.svg)Settings** → *Profiles configuration folder* and open the folder.
- The folder contains a subfolder for each Profile. Open the file `sc4pac-plugins-lock.json` of your current Profile in a text editor and search for the package.
- Change the `"version"` to `"0"` and save the JSON file.
- Clicking *![](_refresh.svg)Update All* will trigger a re-install of the package.

</details>

## Skipping a package upgrade :id=skipping-package-upgrade

Pressing *![](_refresh.svg)Update All* will always upgrade all the packages to their latest version.
Skipping the upgrade for a specific package isn't possible yet.

---
Next up: [CLI](cli)
