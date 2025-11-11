import traci
import math


def lane_direction(lane_id):
    """
    Retourne la direction principale d'une lane en fonction de son angle.
    Renvoie 'unknown' si la lane n'a pas de shape valide.
    """
    try:
        shape = traci.lane.getShape(lane_id)
        if not shape or len(shape) < 2:
            return "unknown"
        x_start, y_start = shape[0]
        x_end, y_end = shape[-1]

        dx = x_end - x_start
        dy = y_end - y_start

        angle = math.degrees(math.atan2(dy, dx)) % 360

        if 45 <= angle < 135:
            return "N"
        elif 135 <= angle < 225:
            return "O"
        elif 225 <= angle < 315:
            return "S"
        else:
            return "E"
    except traci.TraCIException:
        return "unknown"

