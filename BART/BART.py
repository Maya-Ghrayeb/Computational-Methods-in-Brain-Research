
import random
import time

from psychopy import core, data, event, gui, sound, visual


# window and stimulus sizes
from schonbergAPI import SchonbergLabAPI

WIN_WIDTH = 1280
WIN_HEIGHT = 720
POP_TEXTURE_SIZE = (200, 155)
BALL_TEXTURE_SIZE = (596, 720)
INITIAL_BALL_SIZE = (
    int(BALL_TEXTURE_SIZE[0] * 0.2), int(BALL_TEXTURE_SIZE[1] * 0.2))
# ball size increases starting at 20% of screen hight until 100% for condition with maximal 128 pumps

# task configuration
COLOR_LIST = ['yellow', 'orange', 'blue']
MAX_PUMPS = [8, 32, 128]  # three risk types
REPETITIONS = 5  # repetitions of risk
REWARD = 0.05

# keys
KEY_PUMP = 'space'
KEY_NEXT = 'return'
KEY_QUIT = 'escape'

# messages
ABSENT_MESSAGE = 'You\'ve waited to long! The balloon has shrunk. Your temporary earnings are lost.'
FINAL_MESSAGE = 'Well done! You banked a total of {:.2f} €. Thank you for your participation.'


# global objects

# create window
win = visual.Window(
    size=(WIN_WIDTH, WIN_HEIGHT),
    units='pixels',
    color='Black',
    fullscr=False
)
# stimulus
stim = visual.ImageStim(
    win,
    pos=(0, 0),
    size=INITIAL_BALL_SIZE,
    units='pix',
    interpolate=True
)
# text
text = visual.TextStim(
    win,
    color='White',
    height=0.08,
    pos=(0.4, -0.9),
    alignText='right',
    units='norm',
    anchorHoriz='center',
    anchorVert='bottom'
)
remind_return = visual.TextStim(
    win,
    color='White',
    height=0.08,
    pos=(-0.2, -0.9),
    alignText='right',
    units='norm',
    anchorHoriz='right',
    anchorVert='bottom'
)
remind_enter = visual.TextStim(
    win,
    color='White',
    height=0.08,
    pos=(0.2, -0.9),
    alignText='left',
    units='norm',
    anchorHoriz='left',
    anchorVert='bottom'
)
# sounds
slot_machine = sound.Sound('slot_machine4.ogg')
pop_sound = sound.Sound('pop4.ogg')


def showInfoBox():
    """Set up dialog box for subject information."""
    info = {
        'id': '0',
        'age': '0',
        'version': 0.1,
        'gender': ['female', 'male', 'other'],
        'date': data.getDateStr(format="%Y-%m-%d_%H:%M")
    }
    return gui.DlgFromDict(
        title='BART',
        dictionary=info,
        fixed=['version'],
        order=['id', 'age', 'gender', 'date', 'version']
    )


def createTrialHandler(colorList, maxPumps, REPETITIONS, REWARD):
    """Creates a TrialHandler based on colors of balloon and pop stimuli, repetitions of trials and reward value for
    each successful pump. CAVE: color_list and maxPumps must be lists of equal length."""
    # to import balloon and pop images of different colors
    balloonImg = []
    popImg = []
    for color in colorList:
        balloonImg.append(color + 'Balloon.png')
        popImg.append(color + 'Pop.png')
    # create trial list of dictionaries
    trialList = []
    for index in range(len(colorList)):
        trialDef = {
            'balloon_img': balloonImg[index],
            'pop_img': popImg[index],
            'maxPumps': maxPumps[index],
            'reward': REWARD
        }
        trialList.append(trialDef)
    # same order for all subjects
    random.seed(52472)
    trials = data.TrialHandler(
        trialList,
        nReps=REPETITIONS,
        method='fullRandom'
    )
    return trials


def showInstruction(img, wait=30):
    """Show an instruction and wait for a response"""
    instruction = visual.ImageStim(
        win,
        image=img,
        pos=(0, 0),
        size=(2, 2),
        units='norm'
    )
    instruction.draw()
    win.flip()
    respond = event.waitKeys(
        keyList=[KEY_PUMP, KEY_QUIT],
        maxWait=wait
    )
    key = KEY_QUIT if not respond else respond[0]
    return key


def drawText(TextStim, pos, txt, alignment='right'):
    """Takes a PsychoPy TextStim and updates position and text before drawing the stimulus."""
    TextStim.pos = (pos)
    TextStim.setText(txt)
    TextStim.alignText = alignment
    TextStim.draw()


def showImg(img, size, wait=1):
    """Shows an image of spezified size."""
    stim.setImage(img)
    stim.size = size
    stim.draw()
    win.flip()
    core.wait(wait)


def saveData(dataList, file="data.txt"):
    """"Saves all relevant data in txt file."""
    output = '\t'.join(map(str, dataList)) + '\n'
    with open(file, 'a') as outputFile:
        outputFile.write(output.format(dataList))


def drawTrial(ballSize, ballImage, lastMoney, totalMoney):
    """Shows trial setup, i.e. reminders, stimulus, and account balance."""
    stim.size = ballSize
    stim.setImage(ballImage)
    stim.draw()
    drawText(remind_return, (-0.23, -0.9),
             'Press RETURN\nto cash earnings', 'right')
    drawText(remind_enter, (0.23, -0.9),
             'Press ENTER\nto pump', 'left')
    drawText(text, (0.4, -0.6),
             'Last Balloon: \n{:.2f} €'.format(lastMoney))
    drawText(text, (0.4, -0.9),
             'Total Earned: \n{:.2f} €'.format(round(totalMoney, 2)))
    win.flip()


def bart(info):
    worker_key = "3377bab2c0e5b030d36fdc37f6d0d6dd1e73a92b7fb505fbfef6138daccf09be0b57699443554587a92a7a1261991a801e173af8bd1d16c15b58351aa7feeae5"
    api = SchonbergLabAPI(worker_key)
    trials_data=[]
    """Execute experiment"""
    trials = createTrialHandler(COLOR_LIST, MAX_PUMPS, REPETITIONS, REWARD)

    if showInstruction('instructions.png') == KEY_QUIT:
        return

    permBank = 0
    lastTempBank = 0
    # iterate thorugh balloons
    for trialNumber, trial in enumerate(trials):

        # trial default settings
        tempBank = 0  # temporary bank
        pop = False
        nPumps = 0
        continuePumping = True
        increase = 0
        ballSize = INITIAL_BALL_SIZE
        stim.size = ballSize
        response_times = []
        # pump balloon
        while continuePumping and not pop:
            start_time = time.time()
            # increases ball size with each pump
            ballSize = (
                INITIAL_BALL_SIZE[0] + BALL_TEXTURE_SIZE[0] * increase,
                INITIAL_BALL_SIZE[1] + BALL_TEXTURE_SIZE[1] * increase
            )

            drawTrial(ballSize, trial['balloon_img'], lastTempBank, permBank)

            # process response
            respond = event.waitKeys(
                keyList=[KEY_PUMP, KEY_NEXT, KEY_QUIT],
                maxWait=15
            )

            # no response - continue to next balloon
            if not respond:
                drawText(
                    text, (0, 0), ABSENT_MESSAGE, 'center')
                win.flip()
                core.wait(5)
                continuePumping = False

            # escape key pressed
            elif respond[0] == KEY_QUIT:
                return

            #append response time
            end_time = time.time()
            elapsed_time = (end_time - start_time) * 1000
            response_times.append(elapsed_time)

            # cash out key pressed
            if respond[0] == KEY_NEXT:
                lastTempBank = tempBank
                slot_machine.stop()
                slot_machine.play()

                # aninmation: count up to new balance
                newBalance = permBank + tempBank
                while round(permBank, 2) < round(newBalance, 2):
                    permBank += 0.01
                    drawText(text, (0.4, -0.9),
                             'Total Earned:\n{:.2f} €'.format(permBank))
                    win.flip()
                permBank = newBalance
                continuePumping = False

                trial_data = {
                    "trialType": "CashOut",
                    "sumOfGains": permBank,
                    "clicksAmount": nPumps,
                    "responseTimes": response_times
                }

                print(trial_data)
                trials_data.append(trial_data)

            # pump key pressed
            elif respond[0] == KEY_PUMP:
                nPumps += 1

                # determine whether balloon pops or not
                if random.random() < 1.0 / (trial['maxPumps'] - nPumps):
                    pop_sound.stop()
                    pop_sound.play()
                    showImg(trial['pop_img'], POP_TEXTURE_SIZE)
                    lastTempBank = 0
                    pop = True
                    trial_data = {
                        "trialType": "Pump",
                        "sumOfGains": permBank,
                        "clicksAmount": nPumps,
                        "responseTimes": response_times
                    }

                    print(trial_data)
                    trials_data.append(trial_data)
                else:
                    tempBank += REWARD
                    # increase balloon size to fill up other 80%
                    increase += 0.8 / max(MAX_PUMPS)

            # save list of data in txt file
            dataList = [info['id'], trialNumber,
                        trial['maxPumps'], nPumps, pop, '{:.2f}'.format(permBank)]

            saveData(dataList, 'data.txt')
    session_id = api.add_new_session({
        "timestamp": time.time(),
        "email": info['id'],
        "data": trials_data
    })['_id']
    print(api.get_session_with_id(session_id))
    subjectList = [info['id'], info['age'], info['gender'], info['date']]
    saveData(subjectList, 'subjects.txt')

    # final information about reward
    drawText(text, (0, 0),
             FINAL_MESSAGE.format(permBank), 'center')
    win.flip()
    core.wait(5)
    return


def main():
    # dialog for subject information
    infoDlg = showInfoBox()
    info = infoDlg.dictionary
    if infoDlg.OK:
        # start experiment
        bart(info)

    # quit experiment
    win.close()
    core.quit()


if __name__ == "__main__":
    main()
