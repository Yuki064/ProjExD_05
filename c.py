import math
import random
import sys
import time

import pygame as pg


WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm

class Character(pg.sprite.Sprite):
    def __init__(self, hp:int) -> None:
        super().__init__()
        self.hp = hp
    
    def decrease_hp(self):
        self.hp -= 1
        
        return self.hp

class Bird(Character):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int], hp:int):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__(hp)
        
        img0 = pg.transform.rotozoom(pg.image.load(f"ex05_1/fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05_1/fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]

        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)
    
    def get_direction(self) -> tuple[int, int]:
        return self.dire
    

class Enemy(Character):
    """
    敵に関するクラス
    """
    # colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    # img0 = pg.transform.rotozoom(pg.image.load(f"ex05_1/fig/{num}.png"), 0, 1.0)
    imgs = [pg.transform.rotozoom(pg.image.load(f"ex05_1/fig/fantasy_golem{i}.png"),0,0.4) for i in range(1, 3)]

    def __init__(self, bird:Bird, hp:int):
        """
        引数1 bird：攻撃対象のこうかとん
        引数2 hp:敵のHP
        """
        super().__init__(hp)
        
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        
        self.direction = random.choice(["left", "right", "down"])  # 出現位置の方向をランダムに選択
        if self.direction == "left":
            self.rect.x = -self.rect.width  # 左から出現する場合、画面外から出現
            self.rect.y = random.randint(0, HEIGHT - self.rect.height)  # Y座標はランダムに設定
        elif self.direction == "right":
            self.rect.x = WIDTH  # 右から出現する場合、画面外から出現
            self.rect.y = random.randint(0, HEIGHT - self.rect.height)  # Y座標はランダムに設定
        elif self.direction == "down":
            self.rect.x = random.randint(0, WIDTH - self.rect.width)  # X座標はランダムに設定
            self.rect.y = -self.rect.height  # 上から出現する場合、画面外から出現
        self.bird = bird

        self.speed = 2

    def update(self):
        """
        敵を主人公プレイヤーに基づき移動させる
        引数 screen：画面Surface
        """

        self.vx, self.vy = calc_orientation(self.rect, self.bird.rect)
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        
        if self.hp <= 0:
            self.kill()

class Bullet(pg.sprite.Sprite):
    """
    銃に関するクラス
    """
    def __init__(self, bird: Bird, rad = 0):
        """
        銃画像Surfaceを生成する
        引数 bird：銃弾を放つ主人公プレイヤー
        """
        super().__init__()
        self.vx, self.vy = bird.get_direction()
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05_1/fig/tama.png"), angle, 0.05)
        self.vx = math.cos(math.radians(angle + rad))
        self.vy = -math.sin(math.radians(angle + rad))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 15

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
 
    
class NeoBeam(pg.sprite.Sprite):
    def __init__(self, bird: Bird):   # NeoBeamクラスのイニシャライザの引数をbirdとする
        super().__init__()
        self.bird = bird

    def gen_beams(self):
        """
        NeoBeamクラスのgen_beamsメソッドで，
        ‐30°～+31°の角度の範囲で指定ビーム数の分だけBeamオブジェクトを生成し，
        リストにappendする → リストを返す
        """
        start_angle = -30
        end_angle = 31
        
        range_size = end_angle - start_angle
        angle_interval = range_size / (2)

        angles = [start_angle + i * angle_interval for i in range(3)]

        # print(angles)

        neo_beams = [Bullet(self.bird,rad = angles[i]) for i in range(3)]
        return neo_beams
    
class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load("ex05_1/fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()

class Score:
    """
    倒した敵の数をスコアとして表示するクラス
    敵：20点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.score = 0
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def score_up(self, add):
        self.score += add

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.image, self.rect)


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("ex05_1/fig/furoa.png")
    bg_img = pg.transform.scale(bg_img, (WIDTH, HEIGHT))

    score = Score()
    
    bird = Bird(3, (900, 400), 100)
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()


    tmr = 0
    clock = pg.time.Clock()
    while True:
        
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
        
        if score.score >= 100 and score.score < 200:
            if tmr%5==0:
                beams.add(Bullet(bird))
        elif score.score >= 200:
            if tmr%5 == 0:
                """
                発動条件が満たされたら，NeoBeamクラスのイニシャライザに主人公プレイヤーと
                渡し，戻り値のリストをBeamグループに追加する
                """
                n_beams = NeoBeam(bird)
                beam_lst = n_beams.gen_beams()
                # print(f"list in {beam_lst}")
                for i in beam_lst:
                    beams.add(i)
        else: 
            if tmr%10 == 0:
                beams.add(Bullet(bird))

        screen.blit(bg_img, [0, 0])
        """
        ここから下のscoreにかかわる部分をマージしてください
        """
        
        if score.score >= 300:
            if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
                for i in range(10):
                    emys.add(Enemy(bird, 3))
        else:
            if tmr%300 == 0:  # 200フレームに1回，敵機を出現させる   
                for i in range(5):
                    emys.add(Enemy(bird, 2))
            

        for emy in pg.sprite.groupcollide(emys, beams, False, True).keys():
            #hpe = enemey.decrease_hp()
            #print(hpe)
            #if hpe <= 0:
            emy.decrease_hp()
            #print(emy.hp)
            #print("in")
            if emy.hp <= 0:
                
                exps.add(Explosion(emy, 100))  # 爆発エフェクト
                score.score_up(30)  # 10点アップ

                bird.change_img(6, screen)  # こうかとん喜びエフェクト
        
        for emy in pg.sprite.spritecollide(bird, emys, False, False):
            hpb = bird.decrease_hp()
            # print(hpb)
            bird.change_img(8, screen) # こうかとん悲しみエフェクト
            if hpb <= 0:
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
        
        bird.update(key_lst, screen)
        
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()