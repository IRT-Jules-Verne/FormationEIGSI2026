from glob import glob
import os

from setuptools import setup

package_name = 'tb3_livreur'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
        (os.path.join('share', package_name, 'maps'), glob('maps/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ludovic Delval',
    maintainer_email='ludovic.delval@irt-jules-verne.fr',
    description='TP navigation : TurtleBot3 Burger livreur dans l atelier MecaTri.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'mission = tb3_livreur.mission:main',
        ],
    },
)
