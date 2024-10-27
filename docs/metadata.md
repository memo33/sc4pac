# Adding metadata

This page details how to write, for an existing mod, custom metadata that is understood by *sc4pac*.
The metadata is stored in [YAML](https://en.wikipedia.org/wiki/YAML) files which can be edited in any text editor
and consists of *assets* and *packages*, as defined below.

?> An interactive editor for creating metadata files from scratch is available online:
   [YAML editor for sc4pac](https://yamleditorforsc4pac.azurewebsites.net/).
   The editor assists you in obtaining the required metadata and producing syntactically valid metadata files.

?> If you prefer to write the YAML files manually, you can use the [empty template](https://github.com/memo33/sc4pac-tools/blob/main/channel-testing/template-empty.yaml)
   or the [commented example](https://github.com/memo33/sc4pac-tools/blob/main/channel-testing/yaml/templates/package-template-basic.yaml)
   for a quick start.

## Assets

An asset is usually a ZIP file that can be downloaded from the file exchanges.
An asset cannot be installed directly by users of *sc4pac*, but it can provide files for one or multiple installable packages.

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

This is a unique identifier used internally by *sc4pac*.
```yaml
assetId: "dumbledore-hogwarts-castle"
```
You can assign a name of your choice with the following convention:
- lowercase, alphanumeric, hyphenated, no special characters

The above example includes the group `dumbledore` as part of the asset ID to ensure uniqueness of the identifier.

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

### `archiveType`

This is only needed for assets containing Clickteam exe-installers (in particular, not needed for NSIS exe-installers).

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
- lowercase, alphanumeric, hyphenated, no special characters
- Replace all other characters by hyphens.

Examples: `harry-potter`, `bsc`, `peg`, `t-wrecks`, `mattb325`.

### `name`

The name of the package, unique within the group.

```yaml
name: "hogwarts-castle"
```
Conventions:
- lowercase, alphanumeric, hyphenated, no special characters
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
3-digit numbers are used to control load order.

List of subfolders currently in use:

[list-of-subfolders](https://raw.githubusercontent.com/memo33/sc4pac/main/.github/sc4pac-yaml-schema.py ':include :type=code "" :fragment=subfolders-docsify')



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

### `assets` :id=asset-references

Optional list of assets from which to extract files (zero or more).
The `assetId`-references listed here must have been defined and associated with a `url` elsewhere (see [Assets](#assets)).
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
  - If the `include` filter is absent or empty, then by default all files with file type .dat/.sc4model/.sc4lot/.sc4desc/.sc4/.dll are included.
  - If the `exclude` filter is absent or empty, then by default all file types other than .dat/.sc4model/.sc4lot/.sc4desc/.sc4/.dll are excluded.

?> If you anticipate file names changing with future updates of the original upload,
   consider using regular expressions to make the matching more generic, so that the `include` filter keeps working after the updates.

### `info`

Additional descriptive information.
It is mostly optional, but each package should include a one-line `summary` and a link to a `website`, usually the original download page.

A `description` may consist of several paragraphs of contextual information (it should not repeat the `summary`).

> Recommendations:
>
> * Keep the `description` short. Reduce it to information relevant for using the plugin in the game, for example:
>   * Are the buildings growable or ploppable?
>   * RCI types
>   * sizes of growables lots
>   * tilesets if not all are enabled
>
>   Avoid detailed stats like flammability, water consumption, pollution, etc.
> * An introductary sentence or two about real-life architectural context is fine, but it should not take up several paragraphs.
> * Phrase the `description` in a neutral way and avoid first-person.

You should also inform about possible `conflicts`. (If there are none, leave out this field.)

Moreover, you can add a `warning` message that is displayed during the installation process.
This should be used sparingly, for example in case a user has to take action before installing the package.

The `author` field should list the original authors of the content by the names they are known to the community.

The `images` field may contain a list of image links.

```yaml
info:
  summary: School of Witchcraft and Wizardry
  warning: The castle is invisible to Muggles.
  conflicts: Incompatible with Saruman's Isengard Tower
  description: >
    The school is located in the Scottish Highlands.

    It was founded more than 1000 years ago.

    It has a capacity of 900 students who are divided into four houses.
  author: "Albus Dumbledore"
  images:
  - "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Studio_model_of_Hogwarts_at_Leavesden_Studios.jpg/1024px-Studio_model_of_Hogwarts_at_Leavesden_Studios.jpg"
  website: "https://en.wikipedia.org/wiki/Hogwarts"
```

?> The multi-line character `>` in YAML files controls text wrapping.
   See the [YAML format](https://en.wikipedia.org/wiki/YAML#Basic_components).
   Useful alternatives can be `|` or `>-`.
   It is important to pick a suitable text wrapping mode for the style of your `description` in oder to preserve paragraphs.
   Otherwise, all text could end up being displayed on a single line.

?> Use the syntax `` `pkg=hagrid:whomping-willow` `` to refer to another package from within the description or other text fields
   in order to render a link to the package.

## Complete example

Putting together all the pieces, a complete YAML file might look as follows.

[hogwarts-castle](https://raw.githubusercontent.com/memo33/sc4pac/main/docs/hogwarts-castle.yaml ':include :type=code yaml')

A YAML file can contain any number of assets and packages, as long as each asset or package definition is separated by `---` from the previous one.
The location of the YAML files does not matter, so they can be organized in a directory structure.

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

Let us continue with our Hogwarts example and add nightmode variants.
There are two common scenarios:
Either there are two different MaxisNite/DarkNite ZIP files,
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

### `variantDescriptions`

You may add descriptions that explain the different variant choices and help in choosing the right one:

```yaml
variantDescriptions:
  nightmode:
    "standard": "the default MaxisNite style (recommended)"
    "dark": "for use with a DarkNite mod"
```

## Collections

Collections are packages that have an empty list of assets, but only have dependencies.
They do not install any files of their own, but can be used to create themed packs of packages that are easy to install in one go.

One advantage this has is that these collections can receive updates. For example, additional dependencies could be added later on.
Though, some care must be taken to preserve backward compatibility.

Examples: `pkg=madhatter106:midrise-office-pack-collection`, `pkg=memo:essential-fixes`.


---

## Testing your changes

To ensure that your package metadata works as intended, you should test your changes.

- If you created a new YAML file locally on your computer, add its path as a new channel:
  ```sh
  sc4pac channel add "file:///C:/Users/Dumbledore/Desktop/hogwarts-castle.yaml"
  ```
- If you created a YAML file directly on GitHub, click the *Raw* button on GitHub to get the direct link to the YAML file and add it as channel:
  ```sh
  sc4pac channel add "https://raw.githubusercontent.com/memo33/sc4pac/main/docs/hogwarts-castle.yaml"
  ```
- (If you created multiple YAML files, consider using the [`channel build`](cli#channel-build) command.)

Next, install your new package as usual and, if necessary, edit the YAML file until everything works as intended.

!> Most importantly, make sure that the correct files end up in your Plugins folder when installing the package.

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
