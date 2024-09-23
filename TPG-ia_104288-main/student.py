#Diogo Tomás Rebelo Couto 104288 19/11/2023

import asyncio
import getpass
import json
import os
import websockets
import math

from enum import Enum
class DigDugState(Enum):
    NONE = 0
    MOVING_TO_TARGET = 1
    PREPARING = 2
    WAITING_FOR_ENEMY = 3
    CHASE_ENEMY = 4
    # Add more actions here

class GameInfo(object):
    pass

game_info = GameInfo()
game_info.digdug_state = DigDugState.NONE
game_info.target_enemy = None
game_info.target_pos = None
game_info.closest_enemy = None
game_info.target_info = None
game_info.all_corridors = []
game_info.level = 1
game_info.move_count = 0
game_info.last_key = None
game_info.last_pos = [-1, -1]
global fix_rock_movement 
fix_rock_movement = False
game_info.last_target_pos = None
game_info.new_tunnels = []
game_info.map_tunnels = []
game_info.test_corners = []
game_info.test_ver_corners = []
game_info.test_hor_corners = []
game_info.perigo_target = []
game_info.pos_away = 0
fix_rock_test = 0

enemy_infor = {}

######## FUNÇÕES DE CORREDORES
def calculate_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

def reset_leveling():
    game_info.digdug_state = DigDugState.NONE
    game_info.target_enemy = None
    game_info.target_pos = None
    game_info.closest_enemy = None
    game_info.target_info = None
    game_info.all_corridors = []
    game_info.move_count = 0
    game_info.last_key = None
    game_info.last_pos = [0, 0]
    global fix_rock_movement 
    fix_rock_movement = False
    game_info.last_target_pos = None
    game_info.new_tunnels = []
    game_info.test_corners = []
    enemy_infor = {}
    game_info.map_tunnels = []
    game_info.perigo_target = []
    game_info.pos_away = 0
    game_info.fix_rock_test = 0

def find_all_corridors():
    map_width = len(game_info.map)
    map_height = len(game_info.map[0])
    map = game_info.map

    MIN_TUNNEL_SIZE = 5


    # horizontais
    horizontal_corridors = []

    current_tunnel = []
    for i in range(2, map_height):
        current_tunnel = []
        for j in range(map_width):
            if map[j][i] == 0:
                if current_tunnel:
                    continue
                else:
                    game_info.map_tunnels.append([j, i])
                    current_tunnel.append((j, i))
            else: # 1
                if current_tunnel and j - current_tunnel[0][0] > MIN_TUNNEL_SIZE:
                        current_tunnel.append((j-1, i))
                        horizontal_corridors.append(current_tunnel)
                current_tunnel = []

    # verticais
    vertical_corridors = []

    current_tunnel = []
    for j in range(map_width):
        current_tunnel = []
        for i in range(2, map_height):
            if map[j][i] == 0:
                if current_tunnel:
                    continue
                else:
                    game_info.map_tunnels.append([j, i])
                    current_tunnel.append((j, i))
            else: # 1
                if current_tunnel and i - current_tunnel[0][1] > MIN_TUNNEL_SIZE:
                        current_tunnel.append((j, i-1))
                        vertical_corridors.append(current_tunnel)
                current_tunnel = []

    # corners

    corners = []
    print("EU sou tudooo", game_info.map_tunnels)
    for tunnel in vertical_corridors:
        for corner in tunnel:
            if not corner in corners:
                corners.append(corner)
    for tunnel in horizontal_corridors:
        for corner in tunnel:
            if not corner in corners:
                corners.append(corner)

    return horizontal_corridors, vertical_corridors, corners

def find_other_corners(open_positions):
    other_corners = []


    if len(open_positions) > 2:
        for i in range(1, len(open_positions) - 1):
            curr_pos = open_positions[i]
            prev_pos = open_positions[i - 1]
            next_pos = open_positions[i + 1]


            diff_curr_prev = [curr_pos[j] - prev_pos[j] for j in range(2)]
            diff_next_curr = [next_pos[j] - curr_pos[j] for j in range(2)]


            if diff_curr_prev != diff_next_curr:
                other_corners.append(curr_pos)

    return other_corners

######## FUNÇÕES DE INIMIGOS

def update_target_position():
    target_id = game_info.target_info[0] if game_info.target_info else None
    enemies = game_info.state['enemies']
    if target_id:
        for enemy in enemies:
            if enemy['id'] == target_id:
                game_info.target_position = enemy['pos']
                break


def find_closest_enemy():
    enemies = game_info.state['enemies']
    pos_digdug = game_info.state['digdug']
    

    min_distance = float('inf')
    for enemy in enemies:
        enemy_pos = enemy['pos']
        distance = math.sqrt((pos_digdug[0] - enemy_pos[0]) ** 2 + (pos_digdug[1] - enemy_pos[1]) ** 2)
        if distance < min_distance:
            min_distance = distance
            game_info.closest_enemy = enemy
            game_info.target_info = [enemy['id'], enemy['pos']]
            
    
# TODO renomear função


def find_closest_corner_with_enemy():
    find_closest_enemy()
    pos_digdug = game_info.state['digdug']
    min_distance = float('inf')
    closest_corner = None
    classification = "unknown"
    closest_enemy = game_info.target_info[1]

    for corner in game_info.corridor_corners:
        distance = math.sqrt((pos_digdug[0] - corner[0]) ** 2 + (pos_digdug[1] - corner[1]) ** 2)
        enemy_distance = math.sqrt((closest_enemy[0] - corner[0]) ** 2 + (closest_enemy[1] - corner[1]) ** 2)
        if enemy_distance < min_distance:
            min_distance = enemy_distance
            closest_corner = corner

    for corridor in game_info.corridor_vertical:
        if closest_corner in corridor:
            classification = "vertical"
            tunnel = corridor
            break  # Once a match is found exit

    if classification == "unknown":  
        for corridor in game_info.corridor_horizontal:
            if closest_corner in corridor:
                classification = "horizontal"
                tunnel = corridor
                break

    return closest_corner, classification, tunnel





### FUNÇÕES DE MOVIMENTO

def move_towards_position(position):
    state = game_info.state
    pos_digdug = state['digdug']
    print ("sou a pos do digdug",pos_digdug)
    x_diff = position[0] - pos_digdug[0]
    y_diff = position[1] - pos_digdug[1]
    

    if x_diff > 0:
        return "d"  # mover para a direita
    elif x_diff < 0:
        return "a"  # mover para a esquerda
    
    if y_diff > 0:
        return "s"  # mover para baixo
    elif y_diff < 0:
        return "w"  # mover para cima

    return "" 

def move_towards_position_inverse(position):
    state = game_info.state
    pos_digdug = state['digdug']
    print ("sou a pos do digdug",pos_digdug)
    x_diff = position[0] - pos_digdug[0]
    y_diff = position[1] - pos_digdug[1]
    

    if y_diff > 0:
        return "s"  # mover para baixo
    elif y_diff < 0:
        return "w"  # mover para cima
    if x_diff > 0:
        return "d"  # mover para a direita
    elif x_diff < 0:
        return "a"  # mover para a esquerda
    
    return "" 


def update_new_tunnels(position):
    if position not in game_info.new_tunnels and position not in game_info.map_tunnels:
        game_info.new_tunnels.append(position)
    else:
        pass

def avoid_rocks_and_move_inverse():
    pos_digdug = game_info.state['digdug']
    print("TU ESTAS AQUI NO INVERSO")
    global fix_rock_test
   

    print("rock_mov",fix_rock_test)

    if fix_rock_test > 0:
        
        if pos_digdug[1] >= len(game_info.map[0])-1:
            fix_rock_test = 0
            return "w"
        
        fix_rock_test -= 1
        return "s"
    
    if game_info.last_pos == pos_digdug and game_info.last_key != "A":
        if (game_info.last_key == "a" or game_info.last_key == "d"):
            return "w"
        elif (game_info.last_key == "s" or game_info.last_key == "w"):
            fix_rock_test = 3
            return "d"
        else:
            return move_towards_position_inverse(game_info.target_pos)
    else:
        return move_towards_position(game_info.target_pos) 

def avoid_rocks_and_move():
    pos_digdug = game_info.state['digdug']
    global fix_rock_movement

    if fix_rock_movement > 0:
        
        if pos_digdug[1] >= len(game_info.map[0])-1:
            fix_rock_movement = 0
            return "w"
        
        fix_rock_movement -= 1
        return "s"
    
    if game_info.last_pos == pos_digdug and game_info.last_key != "A":
        if (game_info.last_key == "a" or game_info.last_key == "d"):
            return "w"
        elif (game_info.last_key == "s" or game_info.last_key == "w"):
            fix_rock_movement = 3
            return "d"
        else:
            return move_towards_position(game_info.target_pos)
    else:
        return move_towards_position(game_info.target_pos) 

   

def prepare_tunnel():
    enemies = game_info.state['enemies']
    enemy_pos = game_info.target_info[1]
    classification = game_info.target_pos_direction

    pos_digdug = game_info.state['digdug']

    #PREPARE 2 []
    if game_info.pos_away > 0:
        rep = game_info.pos_away - 1
        if game_info.pos_away == 2:
            rep = 0
        
        game_info.pos_away = 0
        prepare_tunnel.index = 0
        if classification == "horizontal":
            if enemy_pos[1] - pos_digdug[1] > 0:
                prepare_tunnel.steps = ["s"]*rep + ["w"]*rep + ["s"]
            else:
                prepare_tunnel.steps = ["w"]*rep + ["s"]*rep + ["w"]
        elif classification == "vertical":
            if enemy_pos[0] - pos_digdug[0] > 0:
                prepare_tunnel.steps = ["d"]*rep + ["a"]*rep + ["d"]
            else:
                prepare_tunnel.steps = ["a"]*rep + ["d"]*rep + ["a"]

    print("PREPARE", prepare_tunnel.index, prepare_tunnel.steps, game_info.last_key)

    key = ""
    if prepare_tunnel.index == len(prepare_tunnel.steps):
        key = prepare_tunnel.steps[prepare_tunnel.index - 1]
    else:
        key = prepare_tunnel.steps[prepare_tunnel.index]

    if prepare_tunnel.index != 0 and game_info.last_key != prepare_tunnel.steps[prepare_tunnel.index - 1]:
        key = prepare_tunnel.steps[prepare_tunnel.index - 1]
        prepare_tunnel.index -= 1    
    prepare_tunnel.index += 1

    for enemy in enemies:
        pos = enemy["pos"]
        if calculate_distance(pos, pos_digdug) < 2:   #se o inimigo estiver "perto" dar skip a um turn key = ""
            return "", False

    return key, len(prepare_tunnel.steps) == prepare_tunnel.index
prepare_tunnel.steps = []
prepare_tunnel.index = 0




def wait_and_shoot():
    pos_digdug = game_info.state.get('digdug')
    classification = game_info.target_pos_direction 
    enemy_pos = game_info.target_info[1]
    if classification == "vertical" and enemy_pos[0] == pos_digdug[0]+2:
        return "A"
    elif classification == "horizontal" and enemy_pos[1] == pos_digdug[1]+2:
        return "A"
    else:
        return "A"
    

def enemy_in_front():
    pos_digdug = game_info.state.get('digdug')
    enemies = game_info.state['enemies']

    for enemy in enemies:
        enemy_pos = enemy["pos"]
        if enemy_pos[0] >= pos_digdug[0] and enemy_pos[0] <= pos_digdug[0] + 3 and pos_digdug[1] == enemy_pos[1] and (game_info.last_key == "d" or game_info.last_key == "A" or game_info.last_key == ""):
            return True
        elif enemy_pos[0] <= pos_digdug[0] and enemy_pos[0] >= pos_digdug[0] - 3 and pos_digdug[1] == enemy_pos[1] and (game_info.last_key == "a" or game_info.last_key == "A" or game_info.last_key == ""):
            return True
        elif enemy_pos[1] <= pos_digdug[1] and enemy_pos[1] >= pos_digdug[1] - 3 and pos_digdug[0] == enemy_pos[0] and (game_info.last_key == "w" or game_info.last_key == "A" or game_info.last_key == ""):
            return True
        elif enemy_pos[1] >= pos_digdug[1] and enemy_pos[1] <= pos_digdug[1] + 3 and pos_digdug[0] == enemy_pos[0] and (game_info.last_key == "s" or game_info.last_key == "A" or game_info.last_key == ""):
            return True
    else:
        return False

################################################################ 
# Funçoes de escolher o target_pos e funções do Action


def find_closest_corner_with_enemy_chasing():
    pos_digdug = game_info.state['digdug']
    min_distance = float('inf')
    closest_corner = None
    classification = "unknown"
    closest_enemy = game_info.target_info[1]
    other_corners = game_info.test_corners

    for corner in other_corners:
        distance = math.sqrt((pos_digdug[0] - corner[0]) ** 2 + (pos_digdug[1] - corner[1]) ** 2)
        enemy_distance = math.sqrt((closest_enemy[0] - corner[0]) ** 2 + (closest_enemy[1] - corner[1]) ** 2)
        if enemy_distance < min_distance:
            min_distance = enemy_distance
            closest_corner = corner


    return closest_corner


def Enemies_incoming():
    if 'digdug' not in game_info.state and 'enemies' not in game_info.state:
        return ""
    else:
        pos_digdug = game_info.state['digdug']
        enemies = game_info.state['enemies']
        if game_info.target_info is None:
            return ""
        elif game_info.target_info is not None:
    
            enemy_id = game_info.target_info[0]

        enemy_info = [enemy for enemy in enemies if enemy.get("id") == enemy_id]
        for enemy in enemies:
            if not enemy_info:
                enemy_pos = enemy["pos"]
                if enemy_pos in game_info.new_tunnels:
                    x_diff = enemy_pos[0] - pos_digdug[0]
                    y_diff = enemy_pos[1] - pos_digdug[1]
                    if x_diff > 0 and y_diff == 0: # minha direita
                        if calculate_distance(enemy_pos, pos_digdug) <= 4:
                            print("teste da distancia", calculate_distance(enemy_pos, pos_digdug))
                            if enemy["dir"] == 3:
                                if game_info.last_key != "d" and game_info.last_key != "A" and calculate_distance(enemy_pos, pos_digdug) <= 4 and calculate_distance(enemy_pos, pos_digdug) > 1:
                                    return "d"
                                elif game_info.last_key != "d" and game_info.last_key != "A" and calculate_distance(enemy_pos, pos_digdug) <= 1:
                                    return "d"
                                else:
                                    return "A"
                            else:
                                return ""
                    if x_diff < 0 and y_diff == 0: # minha esquerda
                        if calculate_distance(enemy_pos, pos_digdug) <= 4:
                            print("teste da distancia", calculate_distance(enemy_pos, pos_digdug))
                            if enemy["dir"] == 1:
                                if game_info.last_key != "a" and game_info.last_key != "A" and calculate_distance(enemy_pos, pos_digdug) <= 4 and calculate_distance(enemy_pos, pos_digdug) > 1:
                                    return "a"
                                elif game_info.last_key != "a" and game_info.last_key != "A" and calculate_distance(enemy_pos, pos_digdug) <= 1:
                                    return "a"
                                else:
                                    return "A"
                            else:
                                return ""
                    if x_diff == 0 and y_diff < 0: #por baixo
                        if calculate_distance(enemy_pos, pos_digdug) <= 4:
                            print("teste da distancia", calculate_distance(enemy_pos, pos_digdug))
                            if enemy["dir"] == 0:
                                if game_info.last_key != "s" and game_info.last_key != "A" and calculate_distance(enemy_pos, pos_digdug) <= 4 and calculate_distance(enemy_pos, pos_digdug) > 1:
                                    return "s"
                                elif game_info.last_key != "s" and game_info.last_key != "A" and calculate_distance(enemy_pos, pos_digdug) <= 1:
                                    return "w"
                                else:
                                    return "A"
                            else:
                                return ""

                    if x_diff == 0 and y_diff > 0: # por ciam
                        if calculate_distance(enemy_pos, pos_digdug) <= 4:
                            print("teste da distancia", calculate_distance(enemy_pos, pos_digdug))
                            if enemy["dir"] == 2:
                                if game_info.last_key != "w" and game_info.last_key != "A" and calculate_distance(enemy_pos, pos_digdug) <= 4 and calculate_distance(enemy_pos, pos_digdug) > 1:
                                    return "w"
                                elif game_info.last_key != "w" and game_info.last_key != "A" and calculate_distance(enemy_pos, pos_digdug) <= 1:
                                    return "s"
                                else:
                                    return "A"
                            else:
                                return ""

            elif enemy["pos"] not in game_info.new_tunnels and enemy["pos"] not in game_info.map_tunnels:
                if calculate_distance(enemy["pos"], pos_digdug) <= 3:
                    game_info.target_position = [0,0]
                    return avoid_rocks_and_move()
            elif enemy_info:
                return ""
        else:
            return ""

def Chase_enemy():
    enemies = game_info.state['enemies']
    pos = game_info.state['digdug']
    enemy_pos = game_info.target_info[1]
    min_distance = float('inf')
    x_diff = enemy_pos[0] - pos[0]
    y_diff = enemy_pos[1] - pos[1]

    enemy_id = game_info.target_info[0]


    enemy_info = [enemy for enemy in enemies if enemy.get("id") == enemy_id]
    if enemy_info:
        update_enemy_target_pos()
        print("sou a pos 1 e pos 2",enemy_pos[0], enemy_pos[1])
        if enemy_pos in game_info.new_tunnels or enemy_pos in game_info.map_tunnels:
            if x_diff > 0: # está a direita
                if y_diff == 0 and enemy_info[0]["dir"] != 3: # estmaos no mesmo y e ele vai no x oposto a mim
                    for corner in game_info.test_corners:
                        if corner[1] == enemy_pos[1]:
                            enemy_distance = math.sqrt((enemy_pos[0] - corner[0]) ** 2 + (enemy_pos[1] - corner[1]) ** 2)
                            if enemy_distance < min_distance:
                                min_distance = enemy_distance
                                closest_corner = corner
                                game_info.target_pos = corner
                    return avoid_rocks_and_move()

                elif y_diff == 0 and enemy_info[0]["dir"] == 3: #vem em minha direçao
                    return "d"
                
                elif y_diff < 0 :
                    for corner in game_info.test_corners:
                        if corner[1] == enemy_pos[1]:
                            enemy_distance = math.sqrt((enemy_pos[0] - corner[0]) ** 2 + (enemy_pos[1] - corner[1]) ** 2)
                            if enemy_distance < min_distance:
                                min_distance = enemy_distance
                                closest_corner = corner
                                game_info.target_pos = corner
                    return avoid_rocks_and_move()
                elif y_diff > 0 :
                    for corner in game_info.test_corners:
                        if corner[1] == enemy_pos[1]:
                            enemy_distance = math.sqrt((enemy_pos[0] - corner[0]) ** 2 + (enemy_pos[1] - corner[1]) ** 2)
                            if enemy_distance < min_distance:
                                min_distance = enemy_distance
                                closest_corner = corner
                                game_info.target_pos = corner
                    return avoid_rocks_and_move()
                
                
            elif x_diff < 0: # está a esquerda
                if y_diff == 0 and enemy_info[0]["dir"] != 1: # estmaos no mesmo y e ele vai no x oposto a mim
                    for corner in game_info.test_corners:
                        if corner[1] == enemy_pos[1]:
                            enemy_distance = math.sqrt((enemy_pos[0] - corner[0]) ** 2 + (enemy_pos[1] - corner[1]) ** 2)
                            if enemy_distance < min_distance:
                                min_distance = enemy_distance
                                closest_corner = corner
                                game_info.target_pos = corner
                    return avoid_rocks_and_move()

                elif y_diff == 0 and enemy_info[0]["dir"] == 1: #vem em minha direçao
                    return "a"
                
                elif y_diff < 0 :
                    for corner in game_info.test_corners:
                        if corner[1] == enemy_pos[1]:
                            enemy_distance = math.sqrt((enemy_pos[0] - corner[0]) ** 2 + (enemy_pos[1] - corner[1]) ** 2)
                            if enemy_distance < min_distance:
                                min_distance = enemy_distance
                                closest_corner = corner
                                game_info.target_pos = corner
                    return avoid_rocks_and_move()
                elif y_diff > 0 :
                    for corner in game_info.test_corners:
                        if corner[1] == enemy_pos[1]:
                            enemy_distance = math.sqrt((enemy_pos[0] - corner[0]) ** 2 + (enemy_pos[1] - corner[1]) ** 2)
                            if enemy_distance < min_distance:
                                min_distance = enemy_distance
                                closest_corner = corner
                                game_info.target_pos = corner
                    return avoid_rocks_and_move()
                
            elif x_diff == 0:
                if enemy_info[0]["dir"] == 0 and y_diff < 0:
                    return "w"
                elif enemy_info[0]["dir"] != 0 and y_diff < 0:
                    for corner in game_info.test_corners:
                        if corner[0] == enemy_pos[0]:
                            enemy_distance = math.sqrt((enemy_pos[0] - corner[0]) ** 2 + (enemy_pos[1] - corner[1]) ** 2)
                            if enemy_distance < min_distance:
                                min_distance = enemy_distance
                                closest_corner = corner
                                game_info.target_pos = corner
                    return avoid_rocks_and_move()


                if enemy_info[0]["dir"] == 2 and y_diff > 0:
                    return "s"
                elif enemy_info[0]["dir"] != 2 and y_diff > 0:
                    for corner in game_info.test_corners:
                        if corner[0] == enemy_pos[0]:
                            enemy_distance = math.sqrt((enemy_pos[0] - corner[0]) ** 2 + (enemy_pos[1] - corner[1]) ** 2)
                            if enemy_distance < min_distance:
                                min_distance = enemy_distance
                                closest_corner = corner
                                game_info.target_pos = corner
                    return avoid_rocks_and_move()

        elif (enemy_pos not in game_info.new_tunnels and enemy_pos not in game_info.map_tunnels) and (enemy_pos[1] != 0 and enemy_pos[1] != 1):
            return ""
            for corner in game_info.test_corners:
                #enemy_info[0]["dir"]  # 0 N 1 E

                if corner[1] == enemy_pos[1]:
                    enemy_distance = math.sqrt((enemy_pos[0] - corner[0]) ** 2 + (enemy_pos[1] - corner[1]) ** 2)
                    if enemy_distance < min_distance:
                        min_distance = enemy_distance
                        closest_corner = corner
                        game_info.target_pos = corner
            return avoid_rocks_and_move()
        elif (enemy_pos[1] == 0 or enemy_pos[1] == 1):
            game_info.target_pos = [0,4]
            return avoid_rocks_and_move_inverse()
        else:
            return ""
    else:
        return ""
        

def  update_enemy_target_pos():
    enemies = game_info.state['enemies']
    enemy_id = game_info.target_info[0]
    enemy_pos = game_info.target_info[1]
    # Check if the enemy ID is still in the current list of enemies
    enemy_info = [enemy for enemy in enemies if enemy.get("id") == enemy_id]
    if enemy_info:
        game_info.target_info[1] = enemy_info[0]["pos"]
    if not enemy_info:
        chose_enemy_and_find_closest_corner()



def chose_enemy_and_find_closest_corner():
    find_closest_enemy()
    closest_corner, classification, tunnel = find_closest_corner_with_enemy()
    if classification == "unknown":
        classification = "vertical"

    pos = game_info.state['digdug']

    pos_away = 3

    rock_above_corner = False

    for rock in game_info.state["rocks"]:
        if rock["pos"][1] == closest_corner[1] and rock["pos"][1] >= pos[1] :    
            rock_above_corner = True

    # Escolher target position
    if classification == "vertical":
        if closest_corner[0] <= pos_away:
            game_info.target_pos = (closest_corner[0] + pos_away, closest_corner[1])
        elif closest_corner[0] >= len(game_info.map[0]) - pos_away:
            game_info.target_pos = (closest_corner[0] - pos_away, closest_corner[1])
        elif pos[0] <= closest_corner[0]:
            game_info.target_pos = (closest_corner[0] - pos_away, closest_corner[1]) if not rock_above_corner else (closest_corner[0] + pos_away, closest_corner[1])
        else:
            game_info.target_pos = (closest_corner[0] + pos_away, closest_corner[1]) if not rock_above_corner else (closest_corner[0] - pos_away, closest_corner[1])

    elif classification == "horizontal":

        other_corner = tunnel[1] if tunnel[0] == closest_corner else tunnel[0]
        if rock_above_corner:
            closest_corner = other_corner
                
        if closest_corner[1] <= pos_away:
            game_info.target_pos = (closest_corner[0], closest_corner[1] + pos_away)
        elif closest_corner[1] >= len(game_info.map) - pos_away:
            game_info.target_pos = (closest_corner[0], closest_corner[1] - pos_away)
        elif pos[1] <= closest_corner[1]:
            game_info.target_pos = (closest_corner[0], closest_corner[1] - pos_away)
        else:
            game_info.target_pos = (closest_corner[0], closest_corner[1] + pos_away)

    game_info.pos_away = pos_away # How far away from the tunnel we are
    game_info.target_pos_direction = classification # Says if the tunnel we are moving to is V or H
    game_info.digdug_state = DigDugState.MOVING_TO_TARGET


# ACTION COMEÇA AQUI

def take_action():
    key = ""
    pos = game_info.state['digdug']
    lives = game_info.state['lives']
    #print(" olaa eu sou target", game_info.target_info)

    # PRE-ACTION
    if game_info.digdug_state == DigDugState.NONE and game_info.target_info == None:
        update_target_position()
        chose_enemy_and_find_closest_corner()
        #print(" olaa eu sou target", game_info.target_info)

    elif game_info.digdug_state == DigDugState.MOVING_TO_TARGET and (game_info.target_info[1] in game_info.new_tunnels or game_info.target_info[1] not in game_info.map_tunnels):
        print(" olaa eu sou target", game_info.target_info[1])
        print("tunnels", game_info.new_tunnels)
        game_info.digdug_state = DigDugState.CHASE_ENEMY

    elif game_info.digdug_state == DigDugState.CHASE_ENEMY and lives == game_info.initial_lives:
        enemies = game_info.state['enemies']
        enemy_id = game_info.target_info[0]
        enemy_pos = game_info.target_info[1]
        
        print(game_info.move_count)
        enemy_info = [enemy for enemy in enemies if enemy.get("id") == enemy_id]
        if not enemy_info:
            game_info.target_info = None
            game_info.digdug_state = DigDugState.NONE
        if enemy_info:
            if enemy_info[0]["pos"] in game_info.map_tunnels:
                chose_enemy_and_find_closest_corner()



    elif game_info.digdug_state == DigDugState.MOVING_TO_TARGET and pos[0] == game_info.target_pos[0] and pos[1] == game_info.target_pos[1]:
        game_info.digdug_state = DigDugState.PREPARING
    
    elif game_info.digdug_state == DigDugState.MOVING_TO_TARGET and game_info.target_pos == game_info.last_target_pos:
        game_info.digdug_state = DigDugState.WAITING_FOR_ENEMY
        game_info.move_count = 0

    elif game_info.digdug_state != DigDugState.NONE and ( lives > 0 and  lives < game_info.initial_lives):
        game_info.initial_lives = lives
        game_info.target_info = None
        game_info.digdug_state = DigDugState.NONE
    elif game_info.digdug_state != DigDugState.NONE and (game_info.level > 0 and  game_info.level < game_info.initial_level):
        game_info.level = game_info.initial_level
        #reset_leveling()


    elif game_info.digdug_state == DigDugState.WAITING_FOR_ENEMY and lives == game_info.initial_lives:

        enemies = game_info.state['enemies']
        enemy_id = game_info.target_info[0]
        enemy_pos = game_info.target_info[1]
        repition = 0
        # After 30 moves, check if the enemy is still present among the enemies
        print(game_info.move_count)
        
        # Check if the enemy ID is still in the current list of enemies
        enemy_info = [enemy for enemy in enemies if enemy.get("id") == enemy_id]
        #print("Olaaaaa ????????",game_info.map_tunnels)
        if (enemy_info and game_info.move_count >= 45 and calculate_distance(pos, enemy_info[0]["pos"]) >= 3) or (enemy_info and enemy_info[0]["pos"] not in game_info.map_tunnels and calculate_distance(pos, enemy_info[0]["pos"]) >= 3 and game_info.move_count >= 15):
            chose_enemy_and_find_closest_corner()  # Choose another corner
            game_info.move_count = 0  # Reset move count
            repition += 1
        if (enemy_info and repition == 3):
            game_info.target_pos = [0,0]
            repition = 0
            game_info.digdug_state = DigDugState.MOVING_TO_TARGET
        elif not enemy_info:
            chose_enemy_and_find_closest_corner()
            game_info.move_count = 0
        else:
            game_info.move_count += 1  # Increment move count       

    elif game_info.digdug_state != DigDugState.NONE:
        enemies = game_info.state['enemies']
        enemy_id = game_info.target_info[0]
        enemy_info = [enemy for enemy in enemies if enemy.get("id") == enemy_id]
        if not enemy_info:
            game_info.target_info = None
            game_info.digdug_state = DigDugState.NONE



    # ACTION
    if game_info.digdug_state == DigDugState.MOVING_TO_TARGET:
        if game_info.target_pos_direction == "vertical":
            key = avoid_rocks_and_move()
            update_new_tunnels(pos)
            find_other_corners(game_info.new_tunnels)
            print(game_info.last_key)
            print(game_info.state)
        elif game_info.target_pos_direction == "horizontal":
            key = avoid_rocks_and_move_inverse()
            update_new_tunnels(pos)
            find_other_corners(game_info.new_tunnels)
            print(game_info.last_key)
            print(game_info.state)
        else:
            key = avoid_rocks_and_move()
            update_new_tunnels(pos)
            find_other_corners(game_info.new_tunnels)
            print(game_info.last_key)
            print(game_info.state)
    elif game_info.digdug_state == DigDugState.CHASE_ENEMY:
        update_enemy_target_pos()
        update_new_tunnels(pos)
        test_key = Chase_enemy()
        print("a test_key",test_key)
        key = test_key
        if key == "":
            chose_enemy_and_find_closest_corner()
        elif key == "None":
            game_info.digdug_state = DigDugState.NONE


    elif game_info.digdug_state == DigDugState.PREPARING:
        key, done = prepare_tunnel()
        update_new_tunnels(pos)
        if done:
            game_info.last_target_pos = game_info.target_pos
            game_info.digdug_state = DigDugState.WAITING_FOR_ENEMY
            game_info.move_count = 0
    elif game_info.digdug_state == DigDugState.WAITING_FOR_ENEMY:
        key = wait_and_shoot()

    # POST-ACTION

    if game_info.last_key != key and key != "A":
        if pos not in game_info.test_corners and pos not in game_info.map_tunnels:
            game_info.test_corners.append(pos)
    
    if Enemies_incoming() != "":
        key = Enemies_incoming()

    if enemy_in_front():
        key = "A"

    print(game_info.digdug_state)
    print("sou o teste enemies incoming", Enemies_incoming())
    update_target_position()
    print("key",key)
    return key

## MAIN LOOP
async def agent_loop(server_address="localhost:8000", agent_name="student"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        while True:
            try:
                state = json.loads(													#?: receive game update, this must be called timely 
                    await websocket.recv()											#?:or your game will get out of sync with the server
                )

                game_info.state = state
                #print(game_info.state)

                if 'map' in state: # Acontece no 1º turno de cada nível
                    reset_leveling()
                    game_info.map = state['map']
                    print(game_info.map)
                    game_info.corridor_horizontal, game_info.corridor_vertical, game_info.corridor_corners = find_all_corridors()
                    game_info.initial_lives = game_info.state['lives']
                    game_info.initial_level = game_info.state['level']

                    print("Novos corredores", game_info.corridor_corners)
                    print("Vertical:", game_info.corridor_vertical)
                    print("Horizontal:", game_info.corridor_horizontal)

                key = ""
                if not "digdug" in state:
                    continue
                key = take_action()
                
                game_info.last_key = key
                game_info.last_pos = game_info.state['digdug']

                await websocket.send(												#?: send key command to server - you must implement
                    json.dumps({"cmd": "key", "key": key})							#?:this send in the AI agent
                ) 
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))

