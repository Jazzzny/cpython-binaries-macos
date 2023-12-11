'''
Python Flat Installer Creator
========================================
This script creates a flat installer package for Python.

By Jazzzny, licensed under GPLv3.
https://www.gnu.org/licenses/gpl-3.0.txt

Usage: python3 Create-Flat-Installer.py <path to Python.mpkg> <path to output folder>
'''

import os
import subprocess
import argparse
import shutil
import time
import platform

# Parse arguments
parser = argparse.ArgumentParser(description='Create a flat installer package for Python.')
parser.add_argument('mpkg', metavar='mpkg', type=str, nargs=1,
                    help='path to Python.mpkg')
parser.add_argument('output', metavar='output', type=str, nargs=1,
                    help='path to output folder')
args = parser.parse_args()

# Count time elapsed
start_time = time.time()

# Set python version using Python.mpkg/Contents/info.plist -> IFMajorVersion + IFMinorVersion
python_version = str(int(subprocess.check_output(['defaults', 'read', os.path.join(args.mpkg[0], 'Contents', 'Info.plist'), 'IFMajorVersion']))) + "." + str(int(subprocess.check_output(['defaults', 'read', os.path.join(args.mpkg[0], 'Contents', 'Info.plist'), 'IFMinorVersion'])))
# CFBundleShortVersionString
python_version_extended = subprocess.check_output(['defaults', 'read', os.path.join(args.mpkg[0], 'Contents', 'Info.plist'), 'CFBundleShortVersionString']).decode().strip()
# Set macOS major version
macos_major_version = platform.mac_ver()[0].split(".")[0]
# Set build version using sw_vers -buildVersion
build_version = subprocess.check_output(['sw_vers', '-buildVersion']).decode().strip()


print("""========================================
Python Flat Installer Creator by Jazzzny
========================================""")

print("Target Python version: " + python_version_extended)
print("Build version: " + build_version)

print()

# .pkg in mpkg -> .pkg in output pkg
pkg_files = {
    f"PythonApplications-{python_version}.pkg" : "Python_Applications.pkg",
    f"PythonUnixTools-{python_version}.pkg" : "Python_Command_Line_Tools.pkg",
    f"PythonDocumentation-{python_version}.pkg" : "Python_Documentation.pkg",
    f"PythonFramework-{python_version}.pkg" : "Python_Framework.pkg",
    f"PythonInstallPip-{python_version}.pkg" : "Python_Install_Pip.pkg",
    f"PythonProfileChanges-{python_version}.pkg" : "Python_Shell_Profile_Updater.pkg",
}

# Verify that all files exist
print("Verifying that all files exist...")
for pkg in pkg_files:
    if not os.path.exists(os.path.join(args.mpkg[0] + "/Contents/Packages", pkg)):
        raise Exception("File " + pkg + " does not exist!")

# Create temp folder in output folder
print("Creating temporary folders...")
if os.path.exists(os.path.join(args.output[0], "temp")):
    shutil.rmtree(os.path.join(args.output[0], "temp"))
os.makedirs(os.path.join(args.output[0], "temp"))

# Create folders for each package
for pkg in pkg_files:
    if os.path.exists(os.path.join(args.output[0], "temp", pkg_files[pkg][:-4])):
        shutil.rmtree(os.path.join(args.output[0], "temp", pkg_files[pkg][:-4]))
    os.makedirs(os.path.join(args.output[0], "temp", pkg_files[pkg][:-4]))

# Create "extracted" folder in each package folder
for pkg in pkg_files:
    if os.path.exists(os.path.join(args.output[0], "temp", pkg_files[pkg][:-4], "extracted")):
        shutil.rmtree(os.path.join(args.output[0], "temp", pkg_files[pkg][:-4], "extracted"))
    os.makedirs(os.path.join(args.output[0], "temp", pkg_files[pkg][:-4], "extracted"))

# Extract each package to its folder - tar -xf <pkg>/Contents/Archive.pax.gz -C <pkg>/extracted
for pkg in pkg_files:
    print("Extracting " + pkg + "...")
    subprocess.check_output(['tar', '-xf', os.path.join(args.mpkg[0], "Contents", "Packages", pkg, "Contents", "Archive.pax.gz"), '-C', os.path.join(args.output[0], "temp", pkg_files[pkg][:-4], "extracted")])

# If package has a Scripts folder, copy it to the package folder and rename "postflight" to "postinstall"
for pkg in pkg_files:
    if os.path.exists(os.path.join(args.mpkg[0], "Contents", "Packages", pkg, "Contents", "Resources", "postflight")):
        print("Copying postflight from " + pkg + "...")
        os.mkdir(os.path.join(args.output[0], "temp", pkg_files[pkg][:-4], "Scripts"))
        shutil.copyfile(os.path.join(args.mpkg[0], "Contents", "Packages", pkg, "Contents", "Resources", "postflight"), os.path.join(args.output[0], "temp", pkg_files[pkg][:-4], "Scripts", "postinstall"))
        os.chmod(os.path.join(args.output[0], "temp", pkg_files[pkg][:-4], "Scripts", "postinstall"), 0o755)

# Special processing for PythonApplications.pkg - move all contents in extracted to subfolder "Python [version]"
os.rename(os.path.join(args.output[0], "temp", "Python_Applications", "extracted"), os.path.join(args.output[0], "temp", "Python_Applications", f"Python {python_version}"))
os.mkdir(os.path.join(args.output[0], "temp", "Python_Applications", "extracted"))
shutil.move(os.path.join(args.output[0], "temp", "Python_Applications", f"Python {python_version}"), os.path.join(args.output[0], "temp", "Python_Applications", "extracted"))

# Create component plist for each package
for pkg in pkg_files:
    print("Creating component plist for " + pkg + "...")
    subprocess.check_output(['pkgbuild', '--analyze', "--root", os.path.join(args.output[0], "temp", pkg_files[pkg][:-4], "extracted"), os.path.join(args.output[0], "temp", pkg_files[pkg][:-4], "component.plist")])

# Create temp pkg for Python_Applications
print("Creating Python_Applications.pkg...")

subprocess.check_output(['pkgbuild', '--root', os.path.join(args.output[0], "temp", "Python_Applications", "extracted"), '--component-plist', os.path.join(args.output[0], "temp", "Python_Applications", "component.plist"), '--identifier', f'org.python.Python.PythonApplications-{python_version}', '--install-location', '/Applications', os.path.join(args.output[0], "temp", "Python_Applications_temp.pkg")])
subprocess.check_output(['pkgutil', '--expand', os.path.join(args.output[0], "temp", "Python_Applications_temp.pkg"), os.path.join(args.output[0], "temp", "Python_Applications_temp_extracted")])

with open(os.path.join(args.output[0], "temp", "Python_Applications_temp_extracted", "PackageInfo"), "r") as f:
    lines = f.readlines()
del lines[-5:-2]
lines[-2] = lines[-2].replace("</relocate>", "<relocate/>")
with open(os.path.join(args.output[0], "temp", "Python_Applications_temp_extracted", "PackageInfo"), "w") as f:
    f.writelines(lines)

subprocess.check_output(['pkgutil', '--flatten', os.path.join(args.output[0], "temp", "Python_Applications_temp_extracted"), os.path.join(args.output[0], "temp", "Python_Applications.pkg")])

os.remove(os.path.join(args.output[0], "temp", "Python_Applications_temp.pkg"))
shutil.rmtree(os.path.join(args.output[0], "temp", "Python_Applications_temp_extracted"))
shutil.rmtree(os.path.join(args.output[0], "temp", "Python_Applications"))

# Create pkg for Python_Command_Line_Tools
print("Creating Python_Command_Line_Tools.pkg...")
subprocess.check_output(['pkgbuild', '--root', os.path.join(args.output[0], "temp", "Python_Command_Line_Tools", "extracted"), '--component-plist', os.path.join(args.output[0], "temp", "Python_Command_Line_Tools", "component.plist"), '--identifier', f'org.python.Python.PythonUnixTools-{python_version}', '--install-location', '/usr/local/bin', os.path.join(args.output[0], "temp", "Python_Command_Line_Tools.pkg")])
shutil.rmtree(os.path.join(args.output[0], "temp", "Python_Command_Line_Tools"))

# Create pkg for Python_Documentation
print("Creating Python_Documentation.pkg...")
subprocess.check_output(['pkgbuild', '--root', os.path.join(args.output[0], "temp", "Python_Documentation", "extracted"), '--component-plist', os.path.join(args.output[0], "temp", "Python_Documentation", "component.plist"), '--identifier', f'org.python.Python.PythonDocumentation-{python_version}', '--install-location', f'/Library/Frameworks/Python.framework/Versions/{python_version}/Resources/English.lproj/Documentation', "--scripts", os.path.join(args.output[0], "temp", "Python_Documentation", "Scripts"), os.path.join(args.output[0], "temp", "Python_Documentation.pkg")])
shutil.rmtree(os.path.join(args.output[0], "temp", "Python_Documentation"))

# Create pkg for Python_Framework
print("Creating Python_Framework.pkg...")
subprocess.check_output(['pkgbuild', '--root', os.path.join(args.output[0], "temp", "Python_Framework", "extracted"), '--component-plist', os.path.join(args.output[0], "temp", "Python_Framework", "component.plist"), '--identifier', f'org.python.Python.PythonFramework-{python_version}', '--install-location', '/Library/Frameworks/Python.framework', "--scripts", os.path.join(args.output[0], "temp", "Python_Framework", "Scripts"), os.path.join(args.output[0], "temp", "Python_Framework.pkg")])
shutil.rmtree(os.path.join(args.output[0], "temp", "Python_Framework"))

# For the remaining packages, they need to be created manually
# Create pkg for Python_Install_Pip
print("Creating Python_Install_Pip.pkg...")
os.mkdir(os.path.join(args.output[0], "temp", "Python_Install_Pip_temp"))

# Write XML
XML_DATA = f"""<?xml version="1.0" encoding="utf-8"?>
<pkg-info overwrite-permissions="true" relocatable="false" identifier="org.python.Python.PythonInstallPip-{python_version}" postinstall-action="none" version="0" format-version="2" generator-version="InstallCmds-834 ({build_version})" auth="root">
    <bundle-version/>
    <upgrade-bundle/>
    <update-bundle/>
    <atomic-update-bundle/>
    <strict-identifier/>
    <relocate/>
    <scripts>
        <postinstall file="./postinstall"/>
    </scripts>
</pkg-info>"""

with open(os.path.join(args.output[0], "temp", "Python_Install_Pip_temp", "PackageInfo"), "w") as f:
    f.write(XML_DATA)

# Copy Scripts folder
shutil.copytree(os.path.join(args.output[0], "temp", "Python_Install_Pip", "Scripts"), os.path.join(args.output[0], "temp", "Python_Install_Pip_temp", "Scripts"))

# pkgutil --flatten
subprocess.check_output(['pkgutil', '--flatten', os.path.join(args.output[0], "temp", "Python_Install_Pip_temp"), os.path.join(args.output[0], "temp", "Python_Install_Pip.pkg")])

# Delete folders
shutil.rmtree(os.path.join(args.output[0], "temp", "Python_Install_Pip_temp"))
shutil.rmtree(os.path.join(args.output[0], "temp", "Python_Install_Pip"))

# Create pkg for Python_Shell_Profile_Updater
print("Creating Python_Shell_Profile_Updater.pkg...")
os.mkdir(os.path.join(args.output[0], "temp", "Python_Shell_Profile_Updater_temp"))

# Write XML
XML_DATA = f"""<?xml version="1.0" encoding="utf-8"?>
<pkg-info overwrite-permissions="true" relocatable="false" identifier="org.python.Python.PythonProfileChanges-{python_version}" postinstall-action="none" version="0" format-version="2" generator-version="InstallCmds-834 ({build_version})" auth="root">
    <bundle-version/>
    <upgrade-bundle/>
    <update-bundle/>
    <atomic-update-bundle/>
    <strict-identifier/>
    <relocate/>
    <scripts>
        <postinstall file="./postinstall"/>
    </scripts>
</pkg-info>"""

with open(os.path.join(args.output[0], "temp", "Python_Shell_Profile_Updater_temp", "PackageInfo"), "w") as f:
    f.write(XML_DATA)

# Copy Scripts folder
shutil.copytree(os.path.join(args.output[0], "temp", "Python_Shell_Profile_Updater", "Scripts"), os.path.join(args.output[0], "temp", "Python_Shell_Profile_Updater_temp", "Scripts"))

# pkgutil --flatten
subprocess.check_output(['pkgutil', '--flatten', os.path.join(args.output[0], "temp", "Python_Shell_Profile_Updater_temp"), os.path.join(args.output[0], "temp", "Python_Shell_Profile_Updater.pkg")])

# Delete folders
shutil.rmtree(os.path.join(args.output[0], "temp", "Python_Shell_Profile_Updater_temp"))
shutil.rmtree(os.path.join(args.output[0], "temp", "Python_Shell_Profile_Updater"))

# Copy resources to temp folder
print("Copying resources...")
shutil.copytree(os.path.join(args.mpkg[0], "Contents", "Resources"), os.path.join(args.output[0], "temp", "Resources"))

# Remove unnecessary files
os.remove(os.path.join(args.output[0], "temp", "Resources", "Description.plist"))
os.remove(os.path.join(args.output[0], "temp", "Resources", "install_certificates.command"))

# Write distribution file
XML_DATA = f"""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<installer-gui-script minSpecVersion="1">
    <title>Python</title>
    <background alignment="left" file="background.jpg" mime-type="image/png"/>
    <welcome file="Welcome.rtf" mime-type="text/richtext"/>
    <readme file="ReadMe.rtf" mime-type="text/richtext"/>
    <license file="License.rtf" mime-type="text/richtext"/>
    <conclusion file="Conclusion.rtf" mime-type="text/richtext"/>
    <options customize="allow" require-scripts="false" rootVolumeOnly="true" hostArchitectures="arm64,x86_64"/>
    <choices-outline>
        <line choice="org.python.Python.PythonFramework-{python_version}"/>
        <line choice="org.python.Python.PythonApplications-{python_version}"/>
        <line choice="org.python.Python.PythonUnixTools-{python_version}"/>
        <line choice="org.python.Python.PythonDocumentation-{python_version}"/>
        <line choice="org.python.Python.PythonProfileChanges-{python_version}"/>
        <line choice="org.python.Python.PythonInstallPip-{python_version}"/>
    </choices-outline>
    <choice id="default"/>
    <choice id="org.python.Python.PythonFramework-{python_version}" visible="true" selected="true" enabled="false" title="Python Framework" description="This package installs Python.framework, that is the python interpreter and the standard library.">
        <pkg-ref id="org.python.Python.PythonFramework-{python_version}"/>
    </choice>
    <choice id="org.python.Python.PythonApplications-{python_version}" visible="true" title="GUI Applications" description="This package installs IDLE (an interactive Python IDE), and Python Launcher.  It also installs a number of examples and demos.">
        <pkg-ref id="org.python.Python.PythonApplications-{python_version}"/>
    </choice>
    <choice id="org.python.Python.PythonUnixTools-{python_version}" visible="true" title="UNIX command-line tools" description="This package installs the unix tools in /usr/local/bin for compatibility with older releases of Python. This package is not necessary to use Python.">
        <pkg-ref id="org.python.Python.PythonUnixTools-{python_version}"/>
    </choice>
    <choice id="org.python.Python.PythonDocumentation-{python_version}" visible="true" title="Python Documentation" description="This package installs the python documentation at a location that is useable for pydoc and IDLE.">
        <pkg-ref id="org.python.Python.PythonDocumentation-{python_version}"/>
    </choice>
    <choice id="org.python.Python.PythonProfileChanges-{python_version}" visible="true" start_selected="true" title="Shell profile updater" description="This packages updates your shell profile to make sure that the Python tools are found by your shell in preference of the system provided Python tools.  If you don't install this package you'll have to add '/Library/Frameworks/Python.framework/Versions/{python_version}/bin' to your PATH by hand.">
        <pkg-ref id="org.python.Python.PythonProfileChanges-{python_version}"/>
    </choice>
    <choice id="org.python.Python.PythonInstallPip-{python_version}" visible="true" start_selected="true" title="Install or upgrade pip" description="This package installs (or upgrades from an earlier version) pip, a tool for installing and managing Python packages.">
        <pkg-ref id="org.python.Python.PythonInstallPip-{python_version}"/>
    </choice>
    <pkg-ref id="org.python.Python.PythonFramework-{python_version}" version="0" auth="Root" onConclusion="none" installKBytes="107932">#Python_Framework.pkg</pkg-ref>
    <pkg-ref id="org.python.Python.PythonApplications-{python_version}" version="0" auth="Root" onConclusion="none" installKBytes="614">#Python_Applications.pkg</pkg-ref>
    <pkg-ref id="org.python.Python.PythonUnixTools-{python_version}" version="0" auth="Root" onConclusion="none" installKBytes="6">#Python_Command_Line_Tools.pkg</pkg-ref>
    <pkg-ref id="org.python.Python.PythonDocumentation-{python_version}" version="0" auth="Root" onConclusion="none" installKBytes="63711">#Python_Documentation.pkg</pkg-ref>
    <pkg-ref id="org.python.Python.PythonProfileChanges-{python_version}" version="0" auth="Root" onConclusion="none" installKBytes="0">#Python_Shell_Profile_Updater.pkg</pkg-ref>
    <pkg-ref id="org.python.Python.PythonInstallPip-{python_version}" version="0" auth="Root" onConclusion="none" installKBytes="0">#Python_Install_Pip.pkg</pkg-ref>
    <pkg-ref id="org.python.Python.PythonFramework-{python_version}">
        <bundle-version>
            <bundle CFBundleShortVersionString="{python_version_extended}" CFBundleVersion="{python_version_extended}" id="org.python.python" path="Versions/{python_version}/Resources/Python.app"/>
        </bundle-version>
    </pkg-ref>
    <pkg-ref id="org.python.Python.PythonApplications-{python_version}">
        <bundle-version>
            <bundle CFBundleShortVersionString="{python_version_extended}" CFBundleVersion="{python_version_extended}" id="org.python.PythonLauncher" path="Python {python_version}/Python Launcher.app"/>
            <bundle CFBundleShortVersionString="{python_version_extended}" CFBundleVersion="{python_version_extended}" id="org.python.IDLE" path="Python {python_version}/IDLE.app"/>
        </bundle-version>
    </pkg-ref>
    <pkg-ref id="org.python.Python.PythonUnixTools-{python_version}">
        <bundle-version/>
    </pkg-ref>
    <pkg-ref id="org.python.Python.PythonDocumentation-{python_version}">
        <bundle-version/>
    </pkg-ref>
    <pkg-ref id="org.python.Python.PythonProfileChanges-{python_version}">
        <bundle-version/>
    </pkg-ref>
    <pkg-ref id="org.python.Python.PythonInstallPip-{python_version}">
        <bundle-version/>
    </pkg-ref>
</installer-gui-script>"""

with open(os.path.join(args.output[0], "temp", "Distribution"), "w") as f:
    f.write(XML_DATA)

# cd into temp folder
os.chdir(os.path.join(args.output[0], "temp"))

# Create flat pkg
print("Creating flat pkg...")
subprocess.check_output(['productbuild', '--distribution', os.path.join(args.output[0], "temp", "Distribution"), '--resource', os.path.join(args.output[0], "temp", "Resources"), os.path.join(args.output[0], f"python-{python_version_extended}-macos{macos_major_version}.pkg")])

# Delete temp folder
print("Deleting temporary files...")
shutil.rmtree(os.path.join(args.output[0], "temp"))

print("Done!")
print("Time elapsed: " + str(round(time.time() - start_time, 2)) + " seconds")