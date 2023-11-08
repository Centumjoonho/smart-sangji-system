import time

class Timer():
    '''
    A class for updating time informaton during mole game

    Attributes:
        time_in_current_pane (time.timestamp): timestamp in miliseconds,
            which is cummulative time in a mole game PanedWindow
        previous_time (time.timestamp): stored time in previous access by
            'update', this attribute will be updated whenever 'update' called
        previous_pane_id (int): pane ID in mole windows
    
    Methods:
        update(current_pane_id) -> time.timestamp: 
            After checking pane_id, it will update time_in_current_pane. 
    '''

    def __init__(self,) -> None:
        self.time_in_current_pane=0.0
        self.previous_time=time.time()
        self.previous_pane_id=None
        
    def update(self, current_pane_id):
        
        if self.previous_pane_id is None:
            self.previous_pane_id = current_pane_id
        
        else:        
            # 만약 이전 pane과 현재 pane이 같다면 시간 업데이트
            if self.previous_pane_id == current_pane_id:
                time_delta = time.time() - self.previous_time
                self.time_in_current_pane += time_delta
            
            # 만약 이전 pane과 현재 pane이 다르다면 시간 제로 세팅
            else:
                self.time_in_current_pane = .0
                self.previous_pane_id = current_pane_id
            
            # previous_time 업데이트
            self.previous_time = time.time()
        
        return self.time_in_current_pane