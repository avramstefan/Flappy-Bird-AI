#!/usr/bin/env python3

import pygame
import random
import time
import pipe_random_gen
import neat
import os
import math


"""Settings"""

NOT_GAME_OVER = 0
GAME_OVER = 1
NUMBER_GENERATIONS = 100

PIPE_START_X_POS = 500

PIPE_THICKNESS = 115
PIPE_UP_END_DISTANCE = 262
PIPE_DOWN_END_DISTANCE = 44
EDGE_OF_ADDING_NEW_PIPE = 100
X_POS_OF_PIPE_APPEARING = 205
FIRST_PIPE = 0
SECOND_PIPE = 1
UP_PIPE = 0
DOWN_PIPE = 1
START_V0 = 30

BIRD_JUMP_DISTANCE = 70
BIRD_START_X_POS = 100
BIRD_START_Y_POS = 350
BIRD_FALL_Y_DISTANCE = 5
BIRD_DISTANCE_TRAVERSED_PER_ITERATION = 5
MAX_BIRD_FALL_V = 28.5

GREAT_REWARD = 0.5
REWARD = 0.1
PUNISHMENT = 1

RELU_ZERO = 0
TIME_SLEEP = 0
TIME_SLEEP_SLOW = 0.018
GEN_SWITCH_TIME = 50
MAX_FITNESS = 0
MAX_FITNESS_EDGE = 2500

pygame.init()

HEIGHT = 700
WIDTH = 500
WHITE = (255, 255, 255)

GEN = 0

window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")

# Preparing the frames for background_gif // splitting the gif into images / frames
back_img = ["images/back_images/frame_0" + str(i) + "_delay-0.03s.gif" for i in range(10)]
for i in range(10, 90):
    back_img.append("images/back_images/frame_" + str(i) + "_delay-0.03s.gif")
back_frames = []
for name in back_img:
    back_frames.append(pygame.image.load(name))

# loading the pipe body
pipe_up = pygame.image.load(r'images/up-down-pipe-edit.png')
pipe_body_up = pygame.image.load(r'images/up-down-pipe-body-edit.png')
pipe_down = pygame.image.load(r'images/down-up-pipe-edit.png')
pipe_body_down = pygame.image.load(r'images/down-up-pipe-body-edit.png')

# Game over image
game_over = pygame.image.load(r'images/gameover.png')

# Bird image
character_straight = pygame.image.load(r'images/red-bird-straight.png')
character_jump = pygame.image.load(r'images/red-bird-jump.png')
character_fall = pygame.image.load(r'images/red-bird-fall.png')

font1 = pygame.font.SysFont('freesanbold.ttf', 50) # font_style

"""End Settings"""

class Bird():
    
    acceleration = 10
    falling = True
    jump_pos = 0
    time = 1
    distance_before_jump = 0

    # Physics -> 
    v0 = 0
    v1 = 0

    def __init__(self, bird_x_pos, bird_y_pos):
        self.bird_x_pos = bird_x_pos
        self.bird_y_pos = bird_y_pos
        
    """
    updating y position:
        y = y0 + v0 * time + (a / 2) * time^2
        
    updating velocity:
        v1 = v0 + a * (t1 - t0);
                    where a = acceleration
                        t1 = momentum at time 1, while t0 = momentum at time 0
                        v1 = velocity at time 1, while v0 = velocity at time 0
    """
    def jump(self):
        self.bird_y_pos = self.bird_y_pos - (self.v0 * self.time -\
            (self.acceleration / 2) * (self.time ** 2))   

        prev_v = self.v1   
        self.v1 = self.v0 - self.acceleration * self.time
        self.v0 = prev_v
        
    def fall(self):
        old_y_pos = self.bird_y_pos
        self.bird_y_pos = self.bird_y_pos + self.v0 * self.time +\
            (self.acceleration / 2) * (self.time ** 2)      
        self.distance_before_jump -= self.bird_y_pos - old_y_pos

        if self.v0 < MAX_BIRD_FALL_V:
            prev_v = self.v1   
            self.v1 = self.v0 + self.acceleration * self.time
            self.v0 = prev_v

    def update_pos(self):
        if self.falling:
            self.fall()
        else:
            self.jump()
            if self.v0 <= 0:
                self.falling = True
                self.distance_before_jump = (BIRD_JUMP_DISTANCE * 3) / 4
                self.v1 = 0
                self.v0 = 0
    
class Pipe():
    
    pipe_slide_units = 2.5
    
    def __init__(self, x_pos, y_pos, x_pos_1, y_pos_1, x_pos_2, y_pos_2):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.x_pos_1 = x_pos_1
        self.y_pos_1 = y_pos_1
        self.x_pos_2 = x_pos_2
        self.y_pos_2 = y_pos_2
        
    def update_pos(self):
        self.x_pos -= self.pipe_slide_units
        self.x_pos_1 -= self.pipe_slide_units
        self.x_pos_2 -= self.pipe_slide_units


#######################################
        
def background_draw(window, birds, pipes, is_game_over, frames_idx, score):
    window.fill(WHITE)
    
    # Background 
    window.blit(back_frames[frames_idx % 89], (-100, 0)) # 0...89 frames
    
    # Character
    if not is_game_over:
        for bird in birds:
            if bird.bird_x_pos <= X_POS_OF_PIPE_APPEARING:
                window.blit(character_straight, (bird.bird_x_pos, bird.bird_y_pos))
            elif (bird.falling and bird.jump_pos == 0) or\
            (bird.falling and bird.bird_y_pos >= bird.jump_pos - (BIRD_JUMP_DISTANCE * 3 / 4)):
                window.blit(character_fall, (bird.bird_x_pos, bird.bird_y_pos))
            elif not bird.falling and bird.bird_y_pos <= bird.jump_pos - (BIRD_JUMP_DISTANCE * 3 / 4):
                window.blit(character_jump, (bird.bird_x_pos, bird.bird_y_pos))
            else:
                window.blit(character_straight, (bird.bird_x_pos, bird.bird_y_pos))
    
    # Pipes
    for i in range(len(pipes)):
        window.blit(pipe_body_up, (pipes[i][0].x_pos_1, pipes[i][0].y_pos_1))
        window.blit(pipe_body_up, (pipes[i][0].x_pos_2, pipes[i][0].y_pos_2))
        window.blit(pipe_up, (pipes[i][0].x_pos, pipes[i][0].y_pos))
        
        window.blit(pipe_body_down, (pipes[i][1].x_pos_1, pipes[i][1].y_pos_1))
        window.blit(pipe_body_down, (pipes[i][1].x_pos_2, pipes[i][1].y_pos_2))
        window.blit(pipe_down, (pipes[i][1].x_pos, pipes[i][1].y_pos))
        
    # Text
    if not is_game_over:
        text1 = font1.render('Score: ' + str(score), True, (10, 255, 255))
        textRect1 = text1.get_rect()
        textRect1.center = (250, 20)
        window.blit(text1, textRect1)
    else:
        for i in range(len(pipes)):
            pipes[i][0].update_pos()
            pipes[i][1].update_pos()
                    
        if pipes[0][0].x_pos <= -PIPE_THICKNESS:
            pipes = pipes[1:]
        
        window.blit(game_over, (10, 200))
        time.sleep(0.015)
        
    # Apply changes
    pygame.display.update()
    
def check_score(bird, pipes):
    if len(pipes) and ((bird.bird_x_pos > pipes[0][0].x_pos + 114 and
        bird.bird_x_pos < pipes[0][0].x_pos + 116) or
        (len(pipes) > 2 and bird.bird_x_pos > pipes[1][0].x_pos + 114 and
         bird.bird_x_pos < pipes[1][0].x_pos + 116)):
        return True
    return False
        
def check_if_collision(x, y, pipes):
    for i in range(len(pipes)):
        if y <= 0 or y + 60 >= 700 or ((x + 60 >= pipes[i][0].x_pos and x <= pipes[i][0].x_pos + PIPE_THICKNESS) and not
                                  (y >= pipes[i][0].y_pos + 261 and y + 60 <= pipes[i][1].y_pos)):
            return True 
    return False

def distance_from_bird_to_pipe(bird_x, bird_y, pipe_x, pipe_y):
    c1 = abs(bird_x - pipe_x)
    c2 = abs(bird_y - pipe_y)
    return int(math.sqrt(c1 ** 2 + c2 ** 2))

def run_game(genomes, config):
    pygame.init()
    
    frames_idx = 0
    score = 0

    # X coordinate starting position for pipes
    x_pipe_start = PIPE_START_X_POS
    
    global window, GEN, TIME_SLEEP_SLOW, TIME_SLEEP, GEN_SWITCH_TIME
    global MAX_FITNESS
    GEN += 1
    
    # if GEN == GEN_SWITCH_TIME:
    #     TIME_SLEEP = TIME_SLEEP_SLOW
    
    pipes = []
    frames_idx += 1
    
    nets = []
    birds = []
    ge = []

    # Creating birds and adding them to be monitorized by NEAT
    for genome_id, genome in genomes:
        genome.fitness = 0  # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(BIRD_START_X_POS, BIRD_START_Y_POS))
        ge.append(genome)

    background_draw(window, birds, pipes, NOT_GAME_OVER, frames_idx, score)
    not_prepared_to_jump = [False for _ in range(len(birds))]
    height_of_jump = [0 for _ in range(len(birds))]
    prev_score = score

    """
    Birds' movement.

    Using a tanh function (not sigmoid). Tanh function has values between -1 and 1.

    Therefore, if the output of the function is higher, then the probability
    that the bird should jump increases. 

    The parameteres that are being considered are represented by the bird's
    coordinates and the distances from the bird to the next pipe (obstacle).
    """
    while True and len(birds):

        index_of_next_pipe = 0
        for bird in birds:
            if len(pipes) and bird.bird_x_pos >= pipes[FIRST_PIPE][UP_PIPE].x_pos + PIPE_THICKNESS:
                index_of_next_pipe = 1
                break
              
        # For each second in the runtime that the bird survives, a point is added to its fitness.
        for x, bird in enumerate(birds): 
            ge[x].fitness += REWARD

            # Move bird on horizontally in the beginning
            if len(pipes) == 0:
                bird.bird_x_pos += 2
                continue

            bird.update_pos()
            if not_prepared_to_jump[x]:
                if bird.falling:# and bird.distance_before_jump <= 0:
                    not_prepared_to_jump[x] = False
                else:
                    continue
            

            # send bird location, top pipe location and bottom pipe location and determine from network whether to jump or not
            output = nets[birds.index(bird)].activate((bird.bird_y_pos,
                    distance_from_bird_to_pipe(bird.bird_x_pos, bird.bird_y_pos,
                    pipes[index_of_next_pipe][0].x_pos, pipes[index_of_next_pipe][0].y_pos + PIPE_UP_END_DISTANCE),
                    distance_from_bird_to_pipe(bird.bird_x_pos, bird.bird_y_pos,
                    pipes[index_of_next_pipe][1].x_pos, pipes[index_of_next_pipe][1].y_pos - PIPE_DOWN_END_DISTANCE)))
            # output = nets[birds.index(bird)].activate((bird.bird_y_pos,
            #                                         abs(bird.bird_y_pos - (pipes[index_of_next_pipe][UP_PIPE].y_pos + PIPE_UP_END_DISTANCE)),
            #                                         abs(bird.bird_y_pos - (pipes[index_of_next_pipe][DOWN_PIPE].y_pos - PIPE_DOWN_END_DISTANCE))))
            # tanh activation function so result will be between in between [-1,1]. over 0.7 means jump
            if output[0] > RELU_ZERO:
                not_prepared_to_jump[x] = True
                height_of_jump[x] = bird.bird_y_pos - BIRD_JUMP_DISTANCE
                bird.jump_pos = bird.bird_y_pos
                bird.falling = False
                bird.v0 = START_V0

        # Creating pipes
        if len(birds) and birds[0].bird_x_pos >= X_POS_OF_PIPE_APPEARING:
            if not len(pipes) or (pipes[FIRST_PIPE][UP_PIPE].x_pos < EDGE_OF_ADDING_NEW_PIPE and len(pipes) == 1):
                if len(pipes) == 1:
                    score += 1
                random_pos = pipe_random_gen.random_pos_up()
                up_pipe_xx = Pipe(x_pipe_start, random_pos, x_pipe_start,
                                  random_pos - 180, x_pipe_start, random_pos - 360)
                down_pipe_xx = Pipe(x_pipe_start, random_pos + 470, x_pipe_start,
                                     random_pos + 680, x_pipe_start, random_pos + 830)
                pipes.append([up_pipe_xx, down_pipe_xx])
            else:
                for i in range(len(pipes)):
                    pipes[i][UP_PIPE].update_pos()
                    pipes[i][DOWN_PIPE].update_pos()
                    
                # The first pipe gets out of the screen (shifted at left), so it's removed
                if pipes[FIRST_PIPE][UP_PIPE].x_pos <= -PIPE_THICKNESS:
                    pipes = pipes[1:]
                
        background_draw(window, birds, pipes, NOT_GAME_OVER, frames_idx, score)
        frames_idx += 1
        time.sleep(TIME_SLEEP)
        
        # check_collisions
        for x, bird in enumerate(birds):
            MAX_FITNESS = max(MAX_FITNESS, ge[birds.index(bird)].fitness)
            
            if check_if_collision(bird.bird_x_pos, bird.bird_y_pos, pipes):
                ge[birds.index(bird)].fitness -= PUNISHMENT
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))
            
        if score > prev_score:
            for x, bird in enumerate(birds): 
                ge[x].fitness += GREAT_REWARD

        if MAX_FITNESS > MAX_FITNESS_EDGE:
            TIME_SLEEP = TIME_SLEEP_SLOW
            
        
def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    
    # Run 50 times
    winner = p.run(run_game, NUMBER_GENERATIONS)

    # show final stats
    print('\nBest genome:\n{!s}'.format(winner))
        
if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)
        
