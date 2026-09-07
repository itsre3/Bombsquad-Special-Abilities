
# ba_meta require api 9

from __future__ import annotations
import random
import _bascenev1
import bascenev1 as bs 
import bascenev1lib
import babase
from bascenev1lib.actor.spaz import Spaz, CurseExplodeMessage
from bascenev1lib.actor.playerspaz import PlayerSpaz, PlayerSpazHurtMessage
from bascenev1lib.actor.bomb import Bomb
from bascenev1._messages import StandMessage
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.actor.popuptext import PopupText
from bascenev1lib.actor.bomb import BombFactory
from typing import TYPE_CHECKING, TypeVar, override, Any


PlayerT = TypeVar('PlayerT', bound='bascenev1.Player')


class Ability:
    def __init__(self, spaz, player, character):
        print(character)
        self.spaz = spaz
        self.player = player
        self.character = character
        self.skill_cooldown = 0
        self.countdown = 3000
        self.text_time = 0
        self.ind_node = bs.newnode('math', 
                             owner = self.spaz.node,
                             attrs = {
                             'input1': (0.4, -1.19, 0),
                             'operation': 'add'
                            })
        self.spaz.node.connectattr('torso_position', self.ind_node, 'input2')
        self.skill_indicator = bs.newnode('text',
                                   owner=self.spaz.node,
                                   attrs={
                                       'text': "0%",
                                       'in_world': True,
                                       'shadow': 0,
                                       'color': (1, 1, 1),
                                       'scale': 0.01,
                                       'h_align': 'center',
                                       'flatness': 1.0
                                   })
        self.ind_node.connectattr('output', self.skill_indicator, 'position')
        self.player.assigninput(bs.InputType.PUNCH_RELEASE, bs.CallStrict(self.skill_activation, self.spaz))
        self.t_time = bs.timer(0.5, self.update_percent, True)
        
    def update_percent(self):
        if self.spaz.node:
            self.text_time += 500
            percent = int((self.text_time/self.countdown) * 100)
            if percent <= 100:
                sr_p = str(percent)
                self.skill_indicator.text = sr_p + "%"
            else:
                pass

    def skill_activation(self, spaz):
        if not spaz.node:
            return
        current_time = int(bs.time() * 1000)
        time_sub = current_time - spaz.last_punch_time_ms
        if time_sub > 2500:
            skill_refresh = current_time - self.skill_cooldown
            if skill_refresh > self.countdown:
                self.skill()
                self.skill_indicator.color = (0, 1, 0)
        
        spaz.node.punch_pressed = False

    def skill(self):
        self.skill_cooldown = int(bs.time() * 1000)
        if self.character == "Snake Shadow":
            self.player.assigninput(bs.InputType.JUMP_PRESS, bs.CallStrict(self.ninja_flip, self.spaz))
            bs.timer(10, bs.CallStrict(self.reconnect), False)
        elif self.character == "Kronk":
            self.spaz._punch_power_scale = 10
            bs.timer(10, bs.CallStrict(self.reconnect), False)
        elif self.character == "Pascal":
            self.spaz.node.hockey = True
            bs.timer(10, bs.CallStrict(self.reconnect), False)
        elif self.character == "Frosty":
            self.spaz.node.handlemessage(
                bs.PowerupMessage('frozone'))
            bs.timer(10, bs.CallStrict(self.reconnect), False)
        elif self.character == "B-9000":
            EmtWave(self.spaz)
            bs.timer(10, bs.CallStrict(self.reconnect), False)
        elif self.character == "Agent Johnson":
            self.agent_stealth(self.spaz.node, "activate")
            bs.timer(10, bs.CallStrict(self.reconnect), False)
        elif self.character == "Grumbledorf":
            CursedDomain(self.spaz)
            bs.timer(10, bs.CallStrict(self.reconnect), False)
        elif self.character == "Zoe":
            CustomControl(spaz=self.spaz, player=self.player)
            bs.timer(10, bs.CallStrict(self.reconnect), False)
        elif self.character == "Taobao Mascot":
            MappedControl(spaz=self.spaz, player=self.player)
            bs.timer(10, bs.CallStrict(self.reconnect), False)
        elif self.character == "Mel":
            self.spaz.bomb_type = "sticky"
            self.spaz.set_bomb_count(10)
            bs.timer(10, bs.CallStrict(self.reconnect), False)

    def reconnect(self):
        if not self.spaz.node:
            return
        self.skill_indicator.color = (0, 0, 0)
        if self.character == "Kronk":
            self.spaz._punch_power_scale = 1
        elif self.character == "Agent Johnson":
            self.agent_stealth(self.spaz.node, "deactivate")
        elif self.character == "Pascal":
            self.spaz.node.hockey = False
        elif self.character == "Mel":
            self.spaz.bomb_type = "normal"
            self.spaz.set_bomb_count(1)
        self.spaz.connect_controls_to_player()
        self.skill_cooldown += 10000
        self.text_time = 0
        self.player.assigninput(bs.InputType.PUNCH_RELEASE, bs.CallStrict(self.skill_activation, self.spaz))
        

    def on_kronk_punch_press(self) -> None:
        if not self.spaz.node or self.spaz.frozen or self.node.knockout > 0.0:
            return
        t_ms = int(bs.time() * 1000.0)
        assert isinstance(t_ms, int)
        if t_ms - self.spaz.last_punch_time_ms >= self.spaz._punch_cooldown:
            if self.spaz.punch_callback is not None:
                self.spaz.punch_callback(self)
            self.spaz._punched_nodes = set()  # Reset this.
            self.spaz.last_punch_time_ms = t_ms
            self.spaz.node.punch_pressed = True
            if not self.spaz.node.hold_node:
                bs.timer(
                    0.1,
                    bs.WeakCall(
                        self.spaz._safe_play_sound,
                        SpazFactory.get().swish_sound,
                        0.8,
                    ),
                )
        self.spaz._turbo_filter_add_press('punch')

    def ninja_flip(self, spaz):
        if spaz.node:
            is_moving = abs(spaz.node.move_up_down) >= 0.75 or abs(spaz.node.move_left_right) >= 0.75
            if not spaz.node.exists(): return
            t = int(bs.basetime() * 1000.0)
            #print(t)
            spaz.last_jump_time_ms = -9999
            if t - spaz.last_jump_time_ms >= spaz._jump_cooldown:
                spaz.node.jump_pressed = True
                if t - spaz.last_punch_time_ms<=95 and is_moving and spaz.node.jump_pressed and spaz.node.punch_pressed:
                	
                    spaz.node.handlemessage("impulse",spaz.node.position[0],spaz.node.position[1]+3.5,spaz.node.position[2],spaz.node.velocity[0],spaz.node.velocity[1],spaz.node.velocity[2],50*spaz.node.run,10*spaz.node.run,0,0,spaz.node.velocity[0],spaz.node.velocity[1],spaz.node.velocity[2])        	
                    spaz.node.handlemessage("impulse",spaz.node.position[0],spaz.node.position[1]+3.6,spaz.node.position[2],spaz.node.velocity[0],spaz.node.velocity[1],spaz.node.velocity[2],50*spaz.node.run,10*spaz.node.run,0,0,spaz.node.velocity[0],spaz.node.velocity[1],spaz.node.velocity[2])
                    spaz.node.handlemessage('impulse',spaz.node.position[0],spaz.node.position[1]+0.001,spaz.node.position[2],0,0.2,0,200,200,0,0,0,5,0)
                spaz.last_jump_time_ms = t
        spaz._turbo_filter_add_press('jump')
        
    def agent_stealth(self, node, state: str):
        if not self.spaz.node:
            return
        prev_name = node.name
        prev_name_color = node.name_color
        if state == "activate":
            node.name = " "
            #node.name_color = None
            node.head_mesh = None
            node.torso_mesh = None
            node.upper_arm_mesh = None
            node.lower_leg_mesh = None
            node.forearm_mesh = None
            node.toes_mesh = None
            node.pelvis_mesh = None
            node.hand_mesh = None
            node.upper_leg_mesh = None
        elif state == "deactivate":
            factory = SpazFactory.get()
            media = factory.get_media(self.character)
            node.name = prev_name
            #node.name_color = prev_name_color
            node.head_mesh = media['head_mesh']
            node.torso_mesh = media['torso_mesh']
            node.upper_arm_mesh = media['upper_arm_mesh']
            node.lower_leg_mesh = media['lower_leg_mesh']
            node.forearm_mesh = media['forearm_mesh']
            node.toes_mesh = media['toes_mesh']
            node.pelvis_mesh = media['pelvis_mesh']
            node.hand_mesh = media['hand_mesh']
            node.upper_leg_mesh = media['upper_leg_mesh']
            
    

def spawn_player_spaz(
    self,
    player: PlayerT,
    position: Sequence[float] = (0, 0, 0),
    angle: float | None = None,
) -> PlayerSpaz:
    # pylint: disable=too-many-locals
    # pylint: disable=cyclic-import
    from bascenev1._gameutils import animate
    from bascenev1._coopsession import CoopSession
    from bascenev1lib.actor.playerspaz import PlayerSpaz

    name = player.getname()
    color = player.color
    highlight = player.highlight

    playerspaztype = getattr(player, 'playerspaztype', PlayerSpaz)
    if not issubclass(playerspaztype, PlayerSpaz):
        playerspaztype = PlayerSpaz
    light_color = babase.normalized_color(color)
    display_color = babase.safecolor(color, target_intensity=0.75)
    spaz = playerspaztype(
        color=color,
        highlight=highlight,
        character=player.character,
        player=player,
    )

    player.actor = spaz
    assert spaz.node

    # If this is co-op and we're on Courtyard or Runaround, add the
    # material that allows us to collide with the player-walls.
    # FIXME: Need to generalize this.
    if isinstance(self.session, CoopSession) and self.map.getname() in [
        'Courtyard',
        'Tower D',
    ]:
        mat = self.map.preloaddata['collide_with_wall_material']
        assert isinstance(spaz.node.materials, tuple)
        assert isinstance(spaz.node.roller_materials, tuple)
        spaz.node.materials += (mat,)
        spaz.node.roller_materials += (mat,)

    spaz.node.name = name
    spaz.node.name_color = display_color
    spaz.connect_controls_to_player()

    # Move to the stand position and add a flash of light.
    spaz.handlemessage(
        StandMessage(
            position, angle if angle is not None else random.uniform(0, 360)
        )
    )
    self._spawn_sound.play(1, position=spaz.node.position)
    light = _bascenev1.newnode('light', attrs={'color': light_color})
    spaz.node.connectattr('position', light, 'position')
    animate(light, 'intensity', {0: 0, 0.25: 1, 0.5: 0})
    _bascenev1.timer(0.5, light.delete)
    
    Ability(spaz=spaz, player=player, character=player.character)
    return spaz


PlayerSpaz.super_handlemessage = PlayerSpaz.handlemessage
def ability_handler(self, msg: Any):
    player = self.getplayer(bs.Player)
    spaz = player.actor
    character = "Snowman"
    if isinstance(msg, bs.FreezeMessage):
        pass
    self.super_handlemessage(msg)

class EmtWave(bs.Actor):
    def __init__(self, owner):
        bs.Actor.__init__(self)
        self.owner = owner
        self.position = self.owner.node.position
        self.emtwavematerial = bs.Material()
        shared = SharedObjects.get()
        
        
        self.emtwavematerial.add_actions(
            conditions = (
                ('they_have_material', shared.player_material)),
            actions = (
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call','at_connect', self.touched_spaz)))
                
        self.node = bs.newnode('region', attrs = {
            'position': (self.position[0], self.position[1], self.position[2]),
            'scale': (0.1, 0.1, 0.1),
            'type': 'sphere',
            'materials': [self.emtwavematerial]
        })
        
        def wave():
            self.visual_radius = bs.newnode('shield', attrs = {
                'position': self.position,
                'color': (0.05, 0.05, 0.1),
                'radius': 0.05
            })
            bs.animate(self.visual_radius, 'radius', {0: 0, 0.3: 2, 0.6: 4, 0.9: 8})
            print('huu')
            bs.timer(1, self.visual_radius.delete)
            bs.animate_array(self.node, 'scale', 3, {0: (0, 0, 0), 1: (8, 8, 8)})
            bs.timer(1, self.node.delete)
            
        bs.timer(0.1, bs.CallStrict(wave))

    def touched_spaz(self):
        node = bs.getcollision().opposingnode
        if node != self.owner.node:
            node.handlemessage('knockout', 500)


class CursedDomain(bs.Actor):
    def __init__(self, owner):
        bs.Actor.__init__(self)
        self.owner = owner
        self.position = self.owner.node.position
        self.curseddomainmat = bs.Material()
        shared = SharedObjects.get()
        self.curseddomainmat.add_actions(
            conditions = (
                ('they_have_material', shared.player_material)),
            actions = (
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('call','at_connect', self.touched_spaz)))
        

        self.node = bs.newnode('region', attrs = {
            'position': (self.position[0], self.position[1], self.position[2]),
            'scale': (2, 1, 1),
            'type': 'sphere',
            'materials': [self.curseddomainmat]
        })
        self.m = bs.newnode('locator', attrs={
                    'shape': 'circleOutline',
                    'position': (self.position[0], self.position[1], self.position[2]),
                    'size': [4],
                    'color': (1,0,0),
                    'opacity': 5,
                    'draw_beauty': False,
                    'additive': True
            })
        self.owner.node.connectattr('position', self.node, 'position')
        self.owner.node.connectattr('position', self.m, 'position')
        self.snode_time = bs.timer(10, self.node.delete)
        self.nodel_time = bs.timer(10, self.m.delete)
        
    
    def touched_spaz(self):
        if not self.owner.is_alive():
            self.node.delete()
            self.m.delete()
            self.snode_time = None
            self.nodel_time = None
            return 
        node = bs.getcollision().opposingnode
        if node != self.owner.node:
            node.handlemessage(bs.PowerupMessage('curse'))


class CustomControl(bs.Actor):
    def __init__(self, spaz, player, position=(0,1,0), velocity=(0,1,0)):
        bs.Actor.__init__(self)
        self.owner = player
        #self.node = spaz.node
        self.spaz = spaz
        self.spaz.disconnect_controls_from_player()
        shared = SharedObjects.get()
        self.bombmaterial = bs.Material()
        ppos = self.spaz.node.position
        
        self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': (ppos[0], ppos[1] + 2.0, ppos[2]),
                    'velocity': velocity,
                    'mesh': bs.getmesh('tnt'),
                    'light_mesh': bs.getmesh('tnt'),
                    'body': 'box',
                    'body_scale': 2,
                    'gravity_scale': 0,
                    'shadow_size': 0.5,
                    'density': 1,
                    'color_texture': bs.gettexture('tnt'),
                    'reflection': 'soft',
                    'reflection_scale': [0.23],
                    'materials': [self.bombmaterial],
                },
            )
        self.m = bs.newnode('locator', owner=self.node, attrs={
                    'shape': 'circle',
                    'size': [1],
                    'color': (1,0,0),
                    'opacity': 5,
                    'draw_beauty': False,
                    'additive': True
            })
        self.node.connectattr('position', self.m, 'position')
        self.set_fly()
        
    def move(self, type_name: str):
        if self.node.exists():
            if type_name == "up":
                self.node.velocity = (0, 60, 0)
            elif type_name == "down":
                self.node.velocity = (0, -60, 0)
            elif type_name == "left":
                self.node.velocity = (-60, 0, 0)
            elif type_name == "right":
                self.node.velocity = (60, 0, 0)
            elif type_name == "go":
                self.node.velocity = (0, 0, -60)
            elif type_name == "back":
                self.node.velocity = (0, 0, 60)
            elif type_name == "reset":
                self.node.velocity = (0.1,0.1,0.1)
    
    def do_nuke(self):
        pos = self.node.position
        bonb = Bomb(
            position = (pos[0], pos[1], pos[2]),
            velocity = (0, 2, 0),
            bomb_type = "impact",
            blast_radius = 10.0,
            bomb_scale = 10.0,
            source_player = self.owner,
            owner = self.spaz.node
            ).autoretain()
        self.node.handlemessage(bs.DieMessage())
        self.spaz.connect_controls_to_player()
    
    def set_fly(self):
        self.owner.assigninput(bs.InputType.PICK_UP_PRESS, bs.CallPartial(self.move, "up"))
        self.owner.assigninput(bs.InputType.JUMP_PRESS, bs.CallPartial(self.move, "down"))
        self.owner.assigninput(bs.InputType.LEFT_PRESS, bs.CallPartial(self.move, "left"))
        self.owner.assigninput(bs.InputType.RIGHT_PRESS, bs.CallPartial(self.move, "right"))
        self.owner.assigninput(bs.InputType.UP_PRESS, bs.CallPartial(self.move, "go"))
        self.owner.assigninput(bs.InputType.DOWN_PRESS, bs.CallPartial(self.move, "back"))
        self.owner.assigninput(bs.InputType.PICK_UP_RELEASE, bs.CallPartial(self.move, "reset"))
        self.owner.assigninput(bs.InputType.JUMP_RELEASE, bs.CallPartial(self.move, "reset"))
        self.owner.assigninput(bs.InputType.LEFT_RELEASE, bs.CallPartial(self.move, "reset"))
        self.owner.assigninput(bs.InputType.RIGHT_RELEASE, bs.CallPartial(self.move, "reset"))
        self.owner.assigninput(bs.InputType.UP_RELEASE, bs.CallPartial(self.move, "reset"))
        self.owner.assigninput(bs.InputType.DOWN_RELEASE, bs.CallPartial(self.move, "reset"))
        self.owner.assigninput(bs.InputType.BOMB_PRESS, bs.CallStrict(self.do_nuke))
        
    
    def handlemessage(self, msg):
        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()
                self.m.delete()
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        else:
            super().handlemessage(msg)
        return None



class CustomBot(Spaz):
    def __init__(self) -> None:
        super().__init__(
            color=(1, 3, 0.5),
            highlight=(0.3, 0.4, 0.7),
            character="Spaz",
            source_player=None,
            start_invincible=False,
            can_accept_powerups=False,
        )
    
    @override
    def handlemessage(self, msg: Any) -> Any:
        # pylint: disable=too-many-branches
        assert not self.expired
        if isinstance(msg, bs.DieMessage):
            super().handlemessage(msg)
        else:
            super().handlemessage(msg)


class MappedControl():
    def __init__(self, spaz, player):
        self.spaz = spaz
        self.owner = player
        self.dummy = CustomBot().autoretain()
        ppos = self.spaz.node.position
        self.dummy.handlemessage(StandMessage(position=(ppos[0], ppos[1], ppos[2])))
        self.parse_move()
        
    
    def parse_move(self):
        killer = bs.timer(9.7, self.kill_bot, False)
        self.owner.assigninput(bs.InputType.PICK_UP_PRESS, self.dummy.on_pickup_press)
        self.owner.assigninput(bs.InputType.JUMP_PRESS, self.dummy.on_jump_press)
        self.owner.assigninput(bs.InputType.PUNCH_PRESS, self.dummy.on_punch_press)
        self.owner.assigninput(bs.InputType.PUNCH_RELEASE, self.dummy.on_punch_release)
        self.owner.assigninput(bs.InputType.UP_DOWN, self.dummy.on_move_up_down)
        self.owner.assigninput(bs.InputType.LEFT_RIGHT, self.dummy.on_move_left_right)
        self.owner.assigninput(
            bs.InputType.HOLD_POSITION_PRESS, self.dummy.on_hold_position_press
        )
        self.owner.assigninput(
            bs.InputType.HOLD_POSITION_RELEASE,
            self.dummy.on_hold_position_release,
        )
        self.owner.assigninput(bs.InputType.PICK_UP_RELEASE, self.dummy.on_pickup_release)
        self.owner.assigninput(bs.InputType.JUMP_RELEASE, self.dummy.on_jump_release)
        self.owner.assigninput(bs.InputType.BOMB_PRESS, self.dummy.on_bomb_press)
        self.owner.assigninput(bs.InputType.BOMB_RELEASE, self.dummy.on_bomb_release)
        self.owner.assigninput(bs.InputType.RUN, self.dummy.on_run)
        
    def kill_bot(self):
        if self.dummy.exists():
            self.dummy.node.delete()
            if self.spaz.exists():
                self.spaz.connect_controls_to_player()

# ba_meta export babase.Plugin
class SpecialAbilities(babase.Plugin):
    def on_app_running(self):
        bs._gameactivity.GameActivity.spawn_player_spaz = spawn_player_spaz
        PlayerSpaz.handlemessage = ability_handler