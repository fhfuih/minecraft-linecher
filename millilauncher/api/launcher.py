"""
Core Minecraft luancher object.
"""
import os
import shutil
import subprocess
from zipfile import ZipFile
from .mcversionslist import MCVersionsList
from .systeminfo import default_minecraft_directory, default_java_directory

_template_script = '{javaw} {extra} -Xmx{maxmem}M -Djava.library.path={natives} -cp {libs} {main} {mcargs}'

class LauncherCore(object):
    """
    Core Minecraft luancher object.
    """
    def __init__(self, mc_dir=default_minecraft_directory, java_dir=default_java_directory):
        self.minecraft_directory = mc_dir
        self.java_directory = java_dir
        if not self.minecraft_directory:
            raise FileNotFoundError('Invalid /.minecraft/ directory.')
        if not self.java_directory:
            raise FileNotFoundError('Invalid javaw.exe directory.')
        self.libraries_directory = os.path.join(self.minecraft_directory, 'libraries')
        self.assets_directory = os.path.join(self.minecraft_directory, 'assets')
        self.version_directory = None
        self.natives_directory = None
        os.chdir(self.minecraft_directory)
        self.versions = MCVersionsList(mc_dir)

        self.extra_argument = '-Dfml.ignoreInvalidMinecraftCertificates=true -Dfml.ignorePatchDiscrepancies=true'

    def launch(self, version_id, username='Steve', maxmem=1024):
        """
        Launch Minecraft
        """
        subprocess.run(self.launch_raw(version_id, username, maxmem))

    # goal: launch(self, version_id, auth[tuple], server, size[tuple])
    def launch_raw(self, version_id, username='Steve', maxmem=1024):
        """
        Returns a cmmand script to launch Minecraft
        """
        version = self.versions.get(version_id)
        if not version:
            raise AttributeError('Version of this id does not exist.')
        self._update_directories(version_id)
        self._extract_natives(version)

        jar = os.path.join(self.minecraft_directory, 'versions', version.jar, version.jar + '.jar')
        libraries = ';'.join([os.path.join(self.libraries_directory, lib.path) for lib in version.libraries]) + ';' + jar
        mcargs = version.minecraft_arguments.format(
            auth_player_name=username, version_name=version_id,
            game_directory=self.minecraft_directory, assets_root=self.assets_directory,
            assets_index_name=version.assets, auth_uuid=0, auth_access_token=0,
            user_type='Legacy', version_type='Legacy')

        return _template_script.format(
            javaw=self.java_directory, extra=self.extra_argument, maxmem=maxmem,
            natives=self.natives_directory, libs=libraries, main=version.main_class, mcargs=mcargs)

    def _update_directories(self, version_id):
        """
        Update version-related directories
        """
        self.version_directory = os.path.join(self.minecraft_directory, 'versions', version_id)
        self.natives_directory = os.path.join(self.version_directory, version_id + '-natives')

    def _extract_natives(self, version):
        """
        Extract natives files from a jar file
        """
        os.chdir(self.libraries_directory)
        exclude_names = set()
        for library in version.extract:
            with ZipFile(library.path) as libzip:
                libzip.extractall(self.natives_directory)
            exclude_names.update(library.exclude)
        os.chdir(self.natives_directory)
        for name in exclude_names:
            shutil.rmtree(name)
        os.chdir(self.minecraft_directory)
