from PyQt5.QtCore import Qt
current_role_index = 0


def getNextRoleId():
    global current_role_index
    current_role_index += 1
    return Qt.UserRole + current_role_index
