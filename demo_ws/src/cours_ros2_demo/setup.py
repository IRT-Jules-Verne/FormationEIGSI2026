from glob import glob
import os

from setuptools import setup

package_name = 'cours_ros2_demo'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ludovic Delval',
    maintainer_email='ludovic.delval@irt-jules-verne.fr',
    description='Package de demonstration du cours ROS 2.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            # point d'entree : nom_executable = module:fonction
            'bonjour = cours_ros2_demo.bonjour:main',
        ],
    },
)
