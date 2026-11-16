"""Lance une demonstration du cours : pixi run cours demo:=4.2 [panne:=1] [derive:=false]

Charge les overlays demo_ws et nav_ws (equivalent de local_setup.ps1 / .bash) puis
execute : ros2 launch cours_ros2_demo cours.launch.py demo:=...
Sans argument : affiche la liste des demonstrations.

Sous Windows, « pixi run » cree la tache dans un groupe de processus a part : un Ctrl+C
tue ce script mais pas ses descendants (ros2 launch et tous les noeuds restent vivants).
Le script place donc ros2 launch dans un « job » Windows configure pour tuer tous ses
processus des que ce script disparait, quelle qu'en soit la raison.
"""

import os
import subprocess
import sys
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ajouter(variable, chemin):
    if os.path.isdir(chemin):
        os.environ[variable] = chemin + os.pathsep + os.environ.get(variable, '')


def charger_overlay(workspace):
    install = os.path.join(RACINE, workspace, 'install')
    if not os.path.isdir(install):
        sys.exit(f"{install} introuvable : lancez d'abord pixi run build et pixi run nav-build")
    for paquet in sorted(os.listdir(install)):
        prefixe = os.path.join(install, paquet)
        if not os.path.isdir(prefixe) or not os.path.isdir(os.path.join(prefixe, 'share')):
            continue
        ajouter('AMENT_PREFIX_PATH', prefixe)
        for site in ('Lib/site-packages', 'lib/python3.12/site-packages', 'lib/site-packages'):
            ajouter('PYTHONPATH', os.path.join(prefixe, *site.split('/')))
        for binaire in ('bin', 'Scripts'):
            ajouter('PATH', os.path.join(prefixe, binaire))


class JobWindows:
    """Job Windows « kill on close » : tout processus assigne (et ses descendants) est tue
    quand le dernier handle du job se ferme, donc au plus tard a la mort de ce script."""

    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self.k32 = ctypes.windll.kernel32
        self.job = self.k32.CreateJobObjectW(None, None)
        if not self.job:
            raise ctypes.WinError()

        class LimiteBase(ctypes.Structure):
            _fields_ = [('PerProcessUserTimeLimit', ctypes.c_int64),
                        ('PerJobUserTimeLimit', ctypes.c_int64),
                        ('LimitFlags', wintypes.DWORD),
                        ('MinimumWorkingSetSize', ctypes.c_size_t),
                        ('MaximumWorkingSetSize', ctypes.c_size_t),
                        ('ActiveProcessLimit', wintypes.DWORD),
                        ('Affinity', ctypes.c_size_t),
                        ('PriorityClass', wintypes.DWORD),
                        ('SchedulingClass', wintypes.DWORD)]

        class CompteursIO(ctypes.Structure):
            _fields_ = [(n, ctypes.c_uint64) for n in (
                'ReadOperationCount', 'WriteOperationCount', 'OtherOperationCount',
                'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]

        class LimiteEtendue(ctypes.Structure):
            _fields_ = [('BasicLimitInformation', LimiteBase),
                        ('IoInfo', CompteursIO),
                        ('ProcessMemoryLimit', ctypes.c_size_t),
                        ('JobMemoryLimit', ctypes.c_size_t),
                        ('PeakProcessMemoryUsed', ctypes.c_size_t),
                        ('PeakJobMemoryUsed', ctypes.c_size_t)]

        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
        JobObjectExtendedLimitInformation = 9
        info = LimiteEtendue()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.k32.SetInformationJobObject(self.job, JobObjectExtendedLimitInformation,
                                                ctypes.byref(info), ctypes.sizeof(info)):
            raise ctypes.WinError()

    def assigner(self, processus):
        import ctypes
        if not self.k32.AssignProcessToJobObject(self.job, int(processus._handle)):
            raise ctypes.WinError()

    def tuer(self):
        self.k32.TerminateJobObject(self.job, 1)


def executer(commande):
    """Execute la commande ; sur Ctrl+C, laisse ros2 launch arreter ses noeuds proprement,
    puis tue tout ce qui resterait."""
    job = None
    if os.name == 'nt':
        try:
            job = JobWindows()
        except OSError as e:  # noqa: BLE001 - on continue sans filet
            print(f'(job Windows indisponible : {e})')
    processus = subprocess.Popen(commande)
    if job is not None:
        job.assigner(processus)
    try:
        return processus.wait()
    except KeyboardInterrupt:
        # ros2 launch a recu le meme Ctrl+C : on lui laisse 10 s pour terminer ses noeuds.
        limite = time.time() + 10.0
        while processus.poll() is None and time.time() < limite:
            time.sleep(0.2)
        if processus.poll() is None:
            print('Arret force des processus restants')
            if job is not None:
                job.tuer()
            else:
                processus.kill()
        return 130


def main():
    for ws in ('demo_ws', 'nav_ws'):
        charger_overlay(ws)
    arguments = sys.argv[1:]
    if not any(a.startswith('demo:=') for a in arguments):
        arguments.append('demo:=liste')
    commande = ['ros2', 'launch', 'cours_ros2_demo', 'cours.launch.py'] + arguments
    print('>', ' '.join(commande))
    sys.exit(executer(commande))


if __name__ == '__main__':
    main()
