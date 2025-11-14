# Metadata format

This page details how to write, for an existing mod, custom metadata that is understood by *sc4pac*.
The metadata is stored in [YAML](https://en.wikipedia.org/wiki/YAML) files which can be edited in any text editor
and consists of *assets* and *packages*, as defined below.

?> If you use the [*sc4pac* STEX integration](https://community.simtropolis.com/forums/topic/763620-simtropolis-x-sc4pac-a-new-way-to-install-plugins/),
   most of this metadata is already created automatically.
   In that case, the information on this page is only needed for customizing the metadata of plugins with more complex installation requirements.

?> An interactive editor for creating and editing metadata files is available online:
   [YAML editor for sc4pac](https://yamleditorforsc4pac.net/).
   The editor assists you in obtaining the required metadata and producing syntactically valid metadata files.

?> If you prefer to write the YAML files manually, you can use the [empty template](https://github.com/memo33/sc4pac-tools/blob/main/channel-testing/template-empty.yaml)
   or the [commented example](https://github.com/memo33/sc4pac-tools/blob/main/channel-testing/yaml/templates/package-template-basic.yaml)
   for a quick start.

## Assets

An asset is a file (most commonly a ZIP file) that can be downloaded from a file exchange.
An asset cannot be installed directly by users of *sc4pac*; rather, assets specify where to find the files called for in a package.

The metadata of an asset is defined by the following properties.

### `url`

This is the direct download link of the ZIP file hosted on a file exchange server.
Get it from the *Download* button of the original upload.

It typically looks like this for files on Simtropolis:
```yaml
url: "https://community.simtropolis.com/files/file/25137-hogwarts-castle/?do=download"
```
or like this on SC4Evermore:
```yaml
url: "https://www.sc4evermore.com/index.php/downloads?task=download.send&id=26:hogwarts-castle"
```
Some uploads on Simtropolis consist of multiple files, in which case the link to a specific file looks like this:
```yaml
url: "https://community.simtropolis.com/files/file/32812-hogwarts-castle/?do=download&r=175227"
```

Conventions:
- Unnecessary query parameters should be removed, such as categories `&catid=26` or other tokens `&confirm=1&t=1&csrfKey=5c0b12346fafafbbbac8ffa45466559a`.
- SC4Evermore URLs should include `www.` as part of their domain.
- Apart from ZIP files, other supported archive formats are 7z, JAR, RAR and NSIS or Clickteam exe-installers.
- Assets may also contain one layer of nested ZIP or other archive files.
- Instead of being wrapped in a ZIP file, assets may also consist of a single DBPF file or DLL file.

### `assetId`

This is a unique identifier used internally by *sc4pac*. The identifier must be globally unique across all assets.
```yaml
assetId: "dumbledore-hogwarts-castle"
```
You can assign a name of your choice with the following convention:
- lowercase, alphanumeric, hyphenated, no special characters

It is recommended to prefix a group name (`dumbledore` in this example) to the asset ID to better ensure uniqueness of the identifier.

### `version` :id=asset-version

The version string should be identical to the one of the original upload.
It is used for determining when an asset has changed, so packages using its files can be reinstalled.
```yaml
version: "1.0"
```

?> Sometimes, the original upload is modified without a change of its version string.
   If necessary, the version of the corresponding asset or package should be incremented nevertheless,
   using the format `1.0`, `1.0-1`, `1.0-2`, `1.0-3`, etc.

### `lastModified`

This is the timestamp of the last-modification date of the upload.
It must have this format:
```yaml
lastModified: "1998-07-29T21:33:57Z"
# lastModified: "1998-07-29T13:33:57-08:00"  # alternative timezone format
```

On Simtropolis, inspect the HTML source code of the download page and search for the `updated_time` property to obtain this timestamp.

On SC4Evermore, grab the *Changed* timestamp from the info box on the download page.

For other sites, use the available info on the download page or, when supported by the server,
use the `Last-Modified` HTTP header of the download URL. Shorthand for cURL users: `curl -I -L '<url>'`.

### `checksum`

An optional sha256 checksum can be added for verifying file integrity.
If present, the checksum of the file is checked directly after download, before extracting the archive.
```yaml
checksum:
  sha256: ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
```

Use this especially for files that are downloaded using http instead of https.
This is required for http files in the default channel, but can be omitted in local channels.

The file hash can be acquired via PowerShell with `Get-FileHash asset.zip | Format-List` or via Bash with `sha256sum asset.zip`.

### `nonPersistentUrl`

When the `url` points to a specific _persistent_ version of a file,
a `nonPersistentUrl` can be added that always points to the _latest_ version of the file.
```yaml
nonPersistentUrl: "https://community.simtropolis.com/files/file/25137-hogwarts-castle/?do=download"
url: "https://github.com/....../v950/hogwarts-castle.zip"
```

?> Mainly, this is useful for DLLs released on GitHub and Simtropolis.
   The `url` would point to the current release on GitHub, while the `nonPersistentUrl` links to Simtropolis.
   The `nonPersistentUrl` is never used for downloading, but can be used by tools to check for updates.
   As the file is downloaded from a specific release on GitHub,
   this avoids intermittent checksum errors when the metadata has not yet been updated after a new release has been uploaded to Simtropolis.

### `archiveType`

This is only needed for assets containing Clickteam exe-installers. It is not needed for NSIS exe-installers.

```yaml
archiveType:
  format: Clickteam
  version: "40"  # possible versions are 40, 35, 30, 24, 20
```

The version number depends on the Clickteam version used when the installer was created.
It must be set correctly or extraction would fail.
You can use the tool `cicdec.exe` to find the correct version number: `cicdec.exe -si <installer.exe>`.

## Packages

A package is a collection of files that *sc4pac* can install automatically if requested by a user.
Packages are exposed to the user when browsing for content.
- The metadata of a package tells *sc4pac* where to obtain the files and how to install them.
- The files are extracted from assets.
- Packages can depend on any number of other packages ("dependencies").

The metadata of a package is defined by the following properties.

### `group`

Package owner, modding group or similar.
```yaml
group: "dumbledore"
```
Convention:
- Lowercase, alphanumeric, hyphenated, no special characters
- Replace all other characters by hyphens.

Examples: `harry-potter`, `bsc`, `peg`, `nybt`, `t-wrecks`, `mattb325`.

### `name`

The name of the package, unique within the group.

```yaml
name: "hogwarts-castle"
```
Conventions:
- Lowercase, alphanumeric, hyphenated, no special characters
- Do not include the `group` within the name itself
- Keep it short and memorable, while unambiguously making clear which upload it refers to.

The unique identifier of a package is of the form `<group>:<name>`, such as `dumbledore:hogwarts-castle`.

### `version` :id=package-version

The version string should be chosen in line with the version of the main asset.
It should be incremented whenever changes are made that make it necessary to reinstall the package.
```yaml
version: "1.0"
```

### `subfolder`

The folder inside the Plugins folder into which the package is installed.
```yaml
subfolder: "620-education"
```
These names are prefixed with 3-digit numbers to control load order.

List of subfolders currently in use:

[list-of-subfolders](https://raw.githubusercontent.com/memo33/sc4pac-actions/main/src/lint.py ':include :type=code "" :fragment=subfolders-docsify')



### `dependencies`

Optional list of package identifiers (zero or more) that are required for this package.
These dependencies will be installed automatically by *sc4pac*.
See [Channel](channel/ ':target=_self') for the available packages.
```yaml
dependencies:
- "hagrid:whomping-willow"
- "lupin:shrieking-shack"
- "madam-hooch:brooms-and-quidditch-equipment"
```

### `conflicting`

Optional list of conflicting packages (zero or more).
When installing a package, *sc4pac* ensures that none of the conflicting packages are installed at the same time.
```yaml
conflicting:
- "saruman:isengard-tower"
```
When two packages are in conflict with each other, it is enough to add the `conflicting` field to just one of them.
The conflict will be recognized automatically for the other, as well.

### `assets` :id=asset-references

Optional list of assets from which to extract files (zero or more).
The `assetId` references listed here must have been defined and associated with a `url` elsewhere (see [Assets](#assets)).
```yaml
assets:
- assetId: "dumbledore-hogwarts-castle"
- assetId: "hagrids-hut"
```
When the package is installed, all the game files contained in the ZIP files
associated with the two assets listed above are extracted and placed inside the Plugins folder.

#### `include`/`exclude`

If not all of the files of an asset are needed, you can add an `include` or `exclude` filter.
Consider a ZIP file with the following contents.
```
Hogwarts_Castle.zip
├── Hogwarts
│   ├── Astronomy Tower.SC4Model
│   ├── Boathouse.SC4Lot
│   ├── Castle.dat
│   ├── Forbidden Forest.dat
│   └── Quidditch pitch.SC4Lot
└── Hogsmeade
    ├── Little Thatched Cottages.dat
    ├── Three Broomsticks Inn.dat
    └── Train Station.dat
```

To `include` just select file names, write:
```yaml
assets:
- assetId: "dumbledore-hogwarts-castle"
  include:
  - "/Astronomy Tower.SC4Model"
  - "/Boathouse.SC4Lot"
  - "/Castle.dat"
```

Include an entire folder with:
```yaml
assets:
- assetId: "dumbledore-hogwarts-castle"
  include:
  - "/Hogwarts/"
```

Or `exclude` unnecessary files with:
```yaml
assets:
- assetId: "dumbledore-hogwarts-castle"
  exclude:
  - "/Forbidden Forest.dat"
  - "/Quidditch pitch.SC4Lot"
  - "/Hogsmeade/"
```

Details:
- The matching is performed against the entire path of a file inside the ZIP archive, such as `/Hogwarts/Castle.dat`.
- You can match on any substring of the path, such as `"arts/Castle"`.
- Use a `/` at the start of file and folder names to avoid unintended mismatches.
- You can even use [regular expressions](https://docs.oracle.com/javase/8/docs/api/java/util/regex/Pattern.html).
  Note that special characters need to be escaped with a backslash: `\.[]{}()<>*+-=!?^$|`.
  The safest way to include a file is to match the entire path, such as `"^/Hogwarts/Castle\\.dat$"`.
- Include all lot files with `"\\.SC4Lot$"`.
- The matching is case-insensitive for file-system independence.
- In any case, always both `include` and `exclude` filters are evaluated.
  If one or both are absent, they default to the following behavior:
  - If the `include` filter is absent or empty, then by default all files with file type .dat/.sc4model/.sc4lot/.sc4desc/.sc4 are included.
  - If the `exclude` filter is absent or empty, then by default all file types other than .dat/.sc4model/.sc4lot/.sc4desc/.sc4 are excluded.
- All extracted files without checksum must be DBPF files.
- The `exclude` patterns are also matched against nested archives to allow skipping nested extraction.

?> If you anticipate file names changing with future updates of the original upload,
   consider using regular expressions to make the matching more generic, so that the `include` filter keeps working after the updates.

### `withChecksum`

In addition to the `include`/`exclude` fields, you can use a `withChecksum` block to only include files if their checksum matches.
This is _required_ for DLL files (code mods) and other non-DBPF file types.
The checksums are verified after the files are extracted from an asset,
but before they are moved from a temporary location into the plugins folder loaded by the game.
```yaml
assets:
- assetId: "dumbledore-hogwarts-castle"
  include:
  - "/Hogwarts/"  # only DBPF files
  withChecksum:
  - include: "/magic.dll"
    sha256: ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
```
In contrast to the `checksum` field of an asset, this is the sha256 hash of the extracted file itself (e.g. hash of the .dll instead of the .zip file).

?> When using `withChecksum`, it is recommended to also add a [`nonPersistentUrl`](#nonPersistentUrl) to the corresponding asset definition.

If a DLL file comes with an INI configuration file, the .ini file requires a checksum as well.
It will be installed into the package subfolder.
Add a warning to inform the user that the INI needs to be manually copied to the root of the Plugins folder:
```yaml
info:
  warning: |-
    This DLL plugin comes with an INI configuration file:

    * `filename.ini`

    To complete the installation, copy this file from the package subfolder into the root directory of your Plugins folder and edit the file to set your preferences.
```

### `info`

Additional descriptive information.
These items are mostly optional, but each package should include a one-line `summary` and a link to a `website` or multiple `websites`, usually the original download page. Other optional items may be included as appropriate.


A `description` may consist of several paragraphs of contextual information (it should not repeat the `summary`).

> Recommendations:
>
> * Keep the `description` short. Reduce it to information relevant for using the plugin in the game, for example:
>   * Are the buildings growable or ploppable?
>   * RCI types
>   * sizes of growable lots
>   * tilesets if not all are enabled
>
> * Avoid detailed stats like flammability, water consumption, pollution, etc.
> * An introductory sentence or two about real-life architectural context is fine, but it should not take up several paragraphs.
> * Phrase the `description` in a neutral way and avoid first-person.

You should also inform about potential incompatibilities: `conflicts`. If there are none, omit this field.
In contrast to the `conflicting` field, this is an information-only text field which is not processed by *sc4pac* in any way.

Moreover, you can add a `warning` message that is displayed during the installation process.
This should be used sparingly and only included in case a user has to take action before or after installing a package.

The `author` field should list the original authors of the content by the names they are known to the community.

The `images` field may contain a list of image links.

```yaml
info:
  summary: School of Witchcraft and Wizardry
  warning: The castle is invisible to Muggles.
  conflicts: Incompatible with Saruman's Isengard Tower
  description: |
    The school is located in the Scottish Highlands.

    It was founded more than 1000 years ago.

    It has a capacity of 900 students who are divided into four houses.
  author: "Albus Dumbledore"
  images:
  - "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Studio_model_of_Hogwarts_at_Leavesden_Studios.jpg/1024px-Studio_model_of_Hogwarts_at_Leavesden_Studios.jpg"
  website: "https://en.wikipedia.org/wiki/Hogwarts"
```

?> The `description` and other text fields use **Markdown** syntax for styling.
   You can use the [Markdown Live Preview](https://markdownlivepreview.com/) to see how your text will be displayed.

?> Use the syntax `` `pkg=hagrid:whomping-willow` `` in order to render a link to another package in the summary or description.

## Complete example

Putting together all the pieces, a complete YAML file might look as follows.

[hogwarts-castle](https://raw.githubusercontent.com/memo33/sc4pac/main/docs/hogwarts-castle.yaml ':include :type=code yaml')

A YAML file can contain any number of assets and packages, as long as each asset or package definition is separated by `---` from the previous one.
The location of the YAML files does not matter, so they can be organized in a directory structure.

?> Alternatively, instead of separating multiple packages and assets by `---`, all definitions can be placed in arrays `packages` and optionally `assets`.
   This has the benefit of allowing the use of YAML *anchors*, *aliases* and *overrides* across packages in the same file to [reduce repetition](https://github.com/memo33/sc4pac-tools/pull/35).

## Options

?> In an installer, options would correspond to check boxes.

If a mod has optional content that is not needed for the main functionality,
you can create a second package that includes just the optional content.
If necessary, it should have a dependency on the first package.

This way, users can decide whether to install the optional package or not.

For example, we can create a package for the optional Quidditch pitch that we excluded from the main package:
```yaml
group: "dumbledore"
name: "hogwarts-castle-quidditch-pitch"
version: "1.0"
subfolder: "660-parks"
dependencies:
- "dumbledore:hogwarts-castle"
assets:
- assetId: "dumbledore-hogwarts-castle"
  include:
  - "/Quidditch pitch.SC4Lot"
```
Note that this package refers to the same `assetId` that we have already defined earlier.

## Variants

?> In an installer, variants would correspond to radio buttons.

Package variants are mutually-exclusive configuration options of a package.
For example, many packages have MaxisNite/DarkNite variants, only one of which should be installed at a time.
The first time a package with a new variant is installed, the user is prompted to choose.

Variants can be defined globally for the entire Plugins folder (e.g. `nightmode`, `driveside`, `roadstyle`, `CAM`),
or locally on a per-package basis (e.g. `kodlovag:uniform-street-lighting-mod:light-color`).

Recommendations:
- Keep the number of variants small.
  Only add a variant if really necessary, but otherwise consider picking a default
  that works for everyone instead of adding another variant.
- Variant names and values should be alphanumeric with hyphens or dots.
  Per-package variants should use a prefix composed of the package identifier `group:package:variant`
  (for example, `kodlovag:uniform-street-lighting-mod:light-color` belongs to `pkg=kodlovag:uniform-street-lighting-mod`).
- If there is a recommended variant, put it first or clearly describe it in order to make it easy to choose.

Continuing with the Hogwarts example, let's add nightmode variants.
There are two common scenarios:
either there are two different MaxisNite/DarkNite ZIP files,
or there is just one ZIP file containing MaxisNite/DarkNite subfolders.

In the first case, we need to define *two* assets (see [Assets](#assets)), one for each ZIP file,
such as `dumbledore-hogwarts-castle-maxisnite` and `dumbledore-hogwarts-castle-darknite`.
Within the package definition, we then refer to the two different assets, depending on the chosen variant:

```yaml
# ... group/name/version/subfolder/info have been skipped here
variants:
- variant: { nightmode: "standard" }
  assets:
  - assetId: "dumbledore-hogwarts-castle-maxisnite"
- variant: { nightmode: "dark" }
  dependencies:
  - "simfox:day-and-nite-mod"
  assets:
  - assetId: "dumbledore-hogwarts-castle-darknite"
```

In the second case, we have a single ZIP file containing subfolders such as `Hogwarts MaxisNite` and `Hogwarts DarkNite`.
Thus, we have just one asset (`dumbledore-hogwarts-castle`) and use `include` filters to select the appropriate files from the ZIP file:
```yaml
# ... group/name/version/subfolder/info have been skipped here
variants:
- variant: { nightmode: "standard" }
  assets:
  - assetId: "dumbledore-hogwarts-castle"
    include:
    - "/Hogwarts MaxisNite/"
- variant: { nightmode: "dark" }
  dependencies:
  - "simfox:day-and-nite-mod"
  assets:
  - assetId: "dumbledore-hogwarts-castle"
    include:
    - "/Hogwarts DarkNite/"
```
Note that the dependency on `pkg=simfox:day-and-nite-mod` is only required for the DarkNite variant.

For complete examples, inspect the metadata of:
- `pkg=mattb325:sunken-library` (two ZIP files for MaxisNite and DarkNite)
- `pkg=mattb325:harbor-clinic` (one ZIP file containing MaxisNite/DarkNite subfolders)

?> If a building has only been published as DarkNite, a MaxisNite variant should be added nevertheless for compatibility.
   This allows to install the building even without a DarkNite mod installed.
   It is just a minor visual conflict that does not affect daytime scenes.
   ```yaml
   assets:
   - assetId: "dumbledore-hogwarts-castle-darknite"  # DN is installed with both variants
   variants:
   - variant: { nightmode: "standard" }
   - variant: { nightmode: "dark" }
     dependencies:
     - "simfox:day-and-nite-mod"
   info:
     conflicts: Only a DarkNite model exists for this building, so the same model is installed with either nightmode setting.
   ```

### `withConditions`

This is an alternative format for specifying multiple variants.
It is often much less verbose in case of complex packages that have many different variant IDs.

```yaml
assets:
- assetId: "dumbledore-hogwarts-castle"
  include:
  - "/Lots/"
  withConditions:
  - ifVariant: { nightmode: "standard" }
    include:
    - "/MN models/"
  - ifVariant: { nightmode: "dark" }
    include:
    - "/DN models/"
  - ifVariant: { roadstyle: "US" }
    include:
    - "/US textures/"
  - ifVariant: { roadstyle: "EU" }
    include:
    - "/EU textures/"
  - ifVariant: { driveside: "right" }
    include: []  # no extra path files for driveside=right
  - ifVariant: { driveside: "left" }
    include:
    - "/z_LHD_paths.dat"
```

Instead of listing all combinations of variants explicitly, the variants are constructed implicitly from the listed `ifVariant` conditions.
This can be more versatile and succinct for packages with many variants, avoiding combinatorial explosion.

For now, this assumes that the variant IDs are all orthogonal to each other, so the user will be prompted to select all of them before installing the package.
The `include` and `exclude` lists for all matching conditions are accumulated.

For example, if a user picks the variants `nightmode: standard`, `roadstyle: EU` and `driveside: left`,
the following files and folders will be extracted from the asset:
```
/Lots/
/MN models/
/EU textures/
/z_LHD_paths.dat
```

One caveat is that one needs to be careful with the `include`/`exclude` patterns to ensure they match for all combinations of variants.
Otherwise, it can easily happen that a pattern does not match, leading to a warning upon installation.

### `variantInfo`

You may add descriptions that explain the different variant choices and help in choosing the right one:

```yaml
variantInfo:
- variantId: "nightmode"
  description: This setting determines whether buildings rendered for DN or MN are installed.
  values:
  - value: "standard"
    description: the default MaxisNite style (recommended)
  - value: "dark"
    description: for use with a DarkNite mod
```

Define a default variant by adding `default: true` to one of the values.

## Collections

Collections are packages that do not include any assets and only have dependencies.
They do not install any files of their own, but can be used to create themed packs of packages that are easy to install in one go.
Imagine a collection that contains a variety of similarly-themed buildings from multiple exchange uploads (and possibly from different creators). 

One advantage this has is that these collections can receive updates - additional dependencies could be added later on.
However, care should be taken to preserve backward compatibility.

Examples: `pkg=madhatter106:midrise-office-pack-collection`, `pkg=memo:essential-fixes`.

## Mod Sets

Mod Sets are JSON files containing a user-selected list of packages to install explicitly.
They have some advantages over collections:

- They can be created and shared easily by any user using the Export/Import buttons.
- When importing a Mod Set, users can select exactly which packages they want to install. They are not forced to install all of them.
- Mod Sets can optionally include pre-selected variant choices and additional channel URLs.

Unlike collections, Mod Sets are not tracked in any channel, so there is no automatic update functionality for them, but there is also less maintenance overhead.


---

## Testing your changes

To ensure that your package metadata works as intended, you should test your changes.

- If you created a new YAML file locally on your computer, add its path as a new channel:
  ```sh
  sc4pac channel add "file:///C:/Users/Dumbledore/Desktop/hogwarts-castle.yaml"
  ```
- You may also test a YAML file in the sc4pac GUI by adding its path as a new channel in the channel definition list:
  ```sh
  file:///C:/Users/Dumbledore/Desktop/hogwarts-castle.yaml
  ```
- If you created a YAML file directly on GitHub, click the *Raw* button on GitHub to get the direct link to the YAML file and add it as channel:
  ```sh
  sc4pac channel add "https://raw.githubusercontent.com/memo33/sc4pac/main/docs/hogwarts-castle.yaml"
  ```
- If you created multiple YAML files, use the [`channel build`](cli#channel-build) command.
  ```sh
    sc4pac channel build --output "channel/json/" "channel/yaml/"
    sc4pac channel add "file:///C:/absolute/path/to/local/channel/json/"
  ```

Next, install your new package as usual and, if necessary, edit the YAML file until everything works as intended.

!> Most importantly, make sure that the correct files end up in your Plugins folder when installing the package.

?> You can use the [`sc4pac test`](cli#test) command to test the successful installation of multiple variants of a package in one go.

?> When you are done, remove the .yaml-channels again, as their contents would conflict with the main channel once you submit your package.
   Removing them also improves performance.


## Submitting your package

To submit your package metadata to the main repository on GitHub:

- You need a GitHub account.
- Go to https://github.com/memo33/sc4pac and hit the *Fork* button to create your own copy.
- Create a [new branch](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-and-deleting-branches-within-your-repository).
- Create a new file, such as `src/yaml/dumbledore/hogwarts-castle.yaml`.
  Add your metadata to the file and create a Pull Request.
  See [Creating new files](https://docs.github.com/en/repositories/working-with-files/managing-files/creating-new-files) for details.
  Also pay attention to the results of the GitHub Action workflow which will validate your YAML file.
  (For first-time contributors, this needs to be triggered manually by the repository owners though.)

Note that submitting your package to the main repository comes with a responsibility for keeping the package up-to-date.
Everyone who installed your package will benefit from it.

---
Next up: [About](about.md)
