from glob import glob
import os

from setuptools import setup

package_name = 'tortue_livreuse'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Les fichiers launch sont copies dans install/ lors du colcon build
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ludovic Delval',
    maintainer_email='ludovic.delval@irt-jules-verne.fr',
    description='TP ROS 2 : une tortue qui livre des colis.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            # nom_de_l_executable = module:fonction
            # -> utilisable avec : ros2 run tortue_livreuse <nom_de_l_executable>
            'navigateur = tortue_livreuse.navigateur:main',
            'fabrique = tortue_livreuse.fabrique:main',
            'carte = tortue_livreuse.carte:main',
        ],
    },
)
