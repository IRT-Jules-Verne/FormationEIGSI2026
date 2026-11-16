from glob import glob
import os

from setuptools import setup

package_name = 'tb3_loopback_sim'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'mondes'), glob('mondes/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ludovic Delval',
    maintainer_email='ludovic.delval@irt-jules-verne.fr',
    description='Simulateur loopback 2D du TurtleBot3 pour le TP navigation.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'simulateur = tb3_loopback_sim.simulateur:main',
            'generer_monde = tb3_loopback_sim.generer_monde:main',
            'pilote = tb3_loopback_sim.pilote:main',
            'veilleur = tb3_loopback_sim.veilleur:main',
        ],
    },
)
