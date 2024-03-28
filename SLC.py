import asyncio
import time


class Lift:
    def __init__(self, current_floor=0, door_open=False, direction=None, motor=False):
        self.current_floor = current_floor
        self.door_open = door_open
        self.direction = direction
        self.motor = motor

    def open_door(self,x):
        print("Opening the door")
        self.door_open = True    
        x[2]=0

    def close_door(self,x, target_floor):
        print("Closing the door")
        self.door_open = False
        x[2]=1
        if target_floor==self.current_floor:
            x[3]=1
        if target_floor>self.current_floor:
            x[4]=1
    
    def down_direction(self):
        print("Moving Downwards")
        self.direction = "Down"

    def up_direction(self):
        print("Moving Upwards")
        self.direction = "Up"

    async def motor_start(self,target_floor,x):
        print("Motor starts")
        self.motor = True
        await self.move_lift(target_floor,x)
    
    def motor_stop(self):
        print("Motor Stops")
        self.motor = False

    async def move_lift(self, target_floor,x):
        print(f"Lift moving from floor {self.current_floor} to floor {target_floor}")

        floor = self.current_floor
        for _ in range(abs(target_floor - self.current_floor)):
            print(self.direction)
            if self.direction == "Up":
                self.current_floor += 1
                time.sleep(1) 
                print(f"Currently on {self.current_floor} floor")
            elif self.direction == "Down":
                self.current_floor -= 1
                time.sleep(1) 
                print(f"Currently on {self.current_floor} floor")

        # Simulate lift movement time
        self.current_floor = target_floor
        x[3]=1
        print(f"Lift arrived at floor {self.current_floor}")

class BDDNode:
    def __init__(self,index, node_type, node_index, successor0=None, successor1=None):
        self.index = index
        self.node_type = node_type
        self.node_index = node_index
        self.successor0 = successor0
        self.successor1 = successor1

class ControlMemoryEntry:
    def __init__(self, index, control=None, imm_transition=False):
        self.index = index
        self.control = control
        self.imm_transition = imm_transition

    async def execute_control(self, lift,x, target_floor):
        # Assuming control is a function that opens the door of the lift
        if self.control == "Y6":
            lift.open_door(x)
        elif self.control == "Y1":
            lift.close_door(x,target_floor)
        elif self.control == "Y2":
            lift.down_direction()
        elif self.control == "Y3":
            lift.up_direction()
        elif self.control == "Y4":
            await lift.motor_start(target_floor,x)
        elif self.control == "Y5":
            lift.motor_stop()
        else:
            print("Unknown control action")

async def slc_driver(Number ,BDD_Table, control_memory, x, lift, target_floor):
    state = 0
    i = Number

    while True:
        state = 0
        index = BDD_Table[i].node_index
        # print(index)
        # print(x[index])
        if BDD_Table[i].node_type == 'x':
            if x[index] == 0:
                i = BDD_Table[i].successor0
            else:
                i = BDD_Table[i].successor1

        elif BDD_Table[i].node_type == 'a':
            state = 1
            if control_memory[index].control is not None:
                await control_memory[index].execute_control(lift,x,target_floor)
                time.sleep(1)                
                print("Executing control action:", control_memory[index].control)
            i = BDD_Table[i].successor1
            
        
        if state and not control_memory[index].imm_transition:
            # print("SLC driver finished execution.")
            return i
                    


async def main():

    lift = Lift()

    # Example BDD table initialization
    BDD_Table = [
        BDDNode(0, 'x', 1, successor0=1, successor1=2),
        BDDNode(1, 'a', 0, successor1=0),
        BDDNode(2, 'a', 1, successor1=3),
        BDDNode(3,'x',2, successor0=6 , successor1=4),
        BDDNode(4,'x', 3, successor0=5, successor1=9),
        BDDNode(5,'x', 4, successor0=7,successor1=8),
        BDDNode(6,'a', 1, successor1=3),
        BDDNode(7,'a', 2, successor1=10),
        BDDNode(8,'a', 3, successor1=11),
        BDDNode(9,'a', 6, successor1=16),
        BDDNode(10,'a', 4,successor1=12),
        BDDNode(11,'a', 4,successor1=12),
        BDDNode(12,'x', 3, successor0=13,successor1=14),
        BDDNode(13,'a', 4,successor1=12),
        BDDNode(14,'a', 5,successor1=15),
        BDDNode(15,'a', 6,successor1=16),
        BDDNode(16,'a', 0,successor1=0)
    ]

    # Example control memory initialization
    control_memory = [
        ControlMemoryEntry(0),
        ControlMemoryEntry(1, control="Y1"),
        ControlMemoryEntry(2, control="Y2", imm_transition=True),
        ControlMemoryEntry(3, control="Y3", imm_transition=True),
        ControlMemoryEntry(4, control="Y4"),
        ControlMemoryEntry(5, control="Y5", imm_transition=True),
        ControlMemoryEntry(6, control="Y6", imm_transition=True)
    ]

    
    while True:
        try:
            x = [0] * 5

            target_floor = int(input("Enter the floor you want to go to (-1 to exit): "))
            if target_floor == -1:
                print("Exiting...")
                break
            x[1]=1

            i=0
            j=1
            while j!=0:
                j = await slc_driver(i ,BDD_Table, control_memory, x,lift,target_floor)
                i=j
                time.sleep(2) 

        except ValueError:
            print("Please enter a valid floor number.")


if __name__ == "__main__":
    asyncio.run(main())
