import threading

from time import sleep

from WindowManager import WindowManager
from MoleManager import MoleManager
from Player import Player

class GameManager():
    
    def __init__(self, num_doles=9) -> None:
        self.num_doles = num_doles

    def start(self,):
        
        # Create window layout
        win_manager = WindowManager()
        win_manager = WindowManager()
        win_manager.get_screenInfo()
        win_manager.display_monitorInfo()
        win_manager.create_windows()

        # Activate the mole game player
        player = Player()
        # player.play_game()
        
        
        # Activate moles window manager
        mole_manager = MoleManager()
        mole_manager.generate_grid_on_moleWindow()
        
        # thread_player = threading.Thread(target=player.play_game)
        # thread_mole_manager = threading.Thread(target=mole_manager.generate_grid_on_moleWindow)
        # thread_player.start()
        # thread_mole_manager.start()


    def pause(self,):
        pass

    def terminate(self,):
        pass


if __name__=='__main__':
    manager = GameManager()
    manager.start()