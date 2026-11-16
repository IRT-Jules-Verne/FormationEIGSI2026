"""Veilleur de démarrage : filet de sécurité pour le lifecycle manager de Nav2.

    ros2 run tb3_loopback_sim veilleur --ros-args -p noeuds:="[map_server, amcl]"

Sous Windows, le lifecycle manager abandonne parfois la mise en route au premier appel
(« Failed to change state for node: map_server » : course entre la découverte DDS et le
premier service appelé). Les nœuds restent alors « unconfigured » et rien ne se passe :
pas de carte, pas de localisation.

Ce nœud attend `delai` secondes, puis vérifie l'état de chaque nœud de `noeuds` avec le
service <noeud>/get_state. Un nœud « unconfigured » est configuré, un nœud « inactive »
est activé, par le service <noeud>/change_state : exactement ce que fait
« ros2 lifecycle set <noeud> configure | activate ». Il recommence toutes les `delai`
secondes, `tentatives` fois au plus, puis se termine. Quand tout est déjà actif, il ne
fait rien d'autre que le dire.
"""

import sys
import time

from lifecycle_msgs.msg import Transition
from lifecycle_msgs.srv import ChangeState, GetState
import rclpy
from rclpy.node import Node

ETATS = {1: 'unconfigured', 2: 'inactive', 3: 'active', 4: 'finalized'}
TRANSITIONS = {'unconfigured': ('configure', Transition.TRANSITION_CONFIGURE),
               'inactive': ('activate', Transition.TRANSITION_ACTIVATE)}


class Veilleur(Node):

    def __init__(self):
        super().__init__('veilleur')
        self.declare_parameter('noeuds', ['map_server', 'amcl'])
        self.declare_parameter('delai', 12.0)
        self.declare_parameter('tentatives', 3)
        self.noeuds = list(self.get_parameter('noeuds').value)
        self.tentatives = int(self.get_parameter('tentatives').value)
        self.tour = 0
        self.mes_clients = {}   # (noeud, service) -> client ; « clients » est réservé par Node
        self.delai = float(self.get_parameter('delai').value)
        self.get_logger().info(
            f'Verification de {self.noeuds} dans {self.delai:.0f} s')

    def appeler(self, nom, type_srv, service, requete):
        cle = (nom, service)
        if cle not in self.mes_clients:
            self.mes_clients[cle] = self.create_client(type_srv, f'/{nom}/{service}')
        client = self.mes_clients[cle]
        if not client.wait_for_service(timeout_sec=2.0):
            self.get_logger().warn(f'/{nom}/{service} : service absent (noeud non lance ?)')
            return None
        futur = client.call_async(requete)
        rclpy.spin_until_future_complete(self, futur, timeout_sec=5.0)
        if not futur.done():
            self.get_logger().warn(f'/{nom}/{service} : pas de reponse en 5 s')
            return None
        return futur.result()

    def etat(self, nom):
        rep = self.appeler(nom, GetState, 'get_state', GetState.Request())
        return None if rep is None else ETATS.get(rep.current_state.id, '?')

    def verifier(self):
        self.tour += 1
        tout_actif = True
        for nom in self.noeuds:
            etat = self.etat(nom)
            # Un nœud peut avoir deux transitions à faire (unconfigured -> inactive -> active)
            while etat in TRANSITIONS:
                tout_actif = False
                libelle, transition = TRANSITIONS[etat]
                self.get_logger().warn(
                    f'{nom} est « {etat} » : le lifecycle manager a abandonne ; '
                    f'j\'envoie « {libelle} » moi-meme (ros2 lifecycle set /{nom} {libelle})')
                req = ChangeState.Request()
                req.transition.id = transition
                rep = self.appeler(nom, ChangeState, 'change_state', req)
                if rep is None or not rep.success:
                    self.get_logger().error(f'{nom} : « {libelle} » a echoue')
                    break
                etat = self.etat(nom)
            if etat != 'active':
                tout_actif = False
        if tout_actif:
            self.get_logger().info(f'Tous les noeuds sont actifs : {self.noeuds}')
            return True
        if self.tour >= self.tentatives:
            self.get_logger().error(
                'Des noeuds ne sont toujours pas actifs. Relancez le launch, ou : '
                'ros2 service call /<lifecycle_manager>/manage_nodes '
                'nav2_msgs/srv/ManageLifecycleNodes "{command: 0}"')
            return True
        return False


def main(args=None):
    rclpy.init(args=args)
    node = Veilleur()
    try:
        # Pas de rclpy.spin(node) ici : les appels de service se font depuis ce fil, avec
        # spin_until_future_complete ; un spin imbriqué dans un callback ne verrait jamais
        # les réponses.
        fini = False
        while not fini and rclpy.ok():
            time.sleep(node.delai)
            fini = node.verifier()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())
