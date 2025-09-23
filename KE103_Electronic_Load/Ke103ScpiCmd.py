from enum import Enum

class KE103SCPICMD(Enum):
    # Identification and Storage
    IDN = "*IDN?"  # Return product information
    SAVE = "*SAV"  # Store the current unit state
    RECALL = "*RCL"  # Recall a stored unit

    # Trigger and System Control
    TRIGGER = "*TRG"  # Simulate an external trigger
    SYSTEM_BEEP = ":SYST:BEEP"  # Control system beep
    SYSTEM_BAUD = ":SYST:BAUD"  # Set baud rate
    STATUS = ":STAT?"  # Query device status

    # Input Control
    INPUT_ON_OFF = ":INP"  # Set or query input state

    # Voltage Commands
    SET_VOLTAGE = ":VOLT"  # Set CV voltage
    QUERY_VOLTAGE = ":VOLT?"  # Query CV voltage
    MAX_VOLTAGE = ":VOLT:UPP?"  # Query max voltage
    MIN_VOLTAGE = ":VOLT:LOW?"  # Query min voltage

    # Current Commands
    SET_CURRENT = ":CURR"  # Set CC current
    QUERY_CURRENT = ":CURR?"  # Query CC current
    MAX_CURRENT = ":CURR:UPP?"  # Query max current
    MIN_CURRENT = ":CURR:LOW?"  # Query min current

    # Resistance Commands
    SET_RESISTANCE = ":RES"  # Set CR resistance
    QUERY_RESISTANCE = ":RES?"  # Query CR resistance
    MAX_RESISTANCE = ":RES:UPP?"  # Query max resistance
    MIN_RESISTANCE = ":RES:LOW?"  # Query min resistance

    # Power Commands
    SET_POWER = ":POW"  # Set CW power
    QUERY_POWER = ":POW?"  # Query CW power
    MAX_POWER = ":POW:UPP?"  # Query max power
    MIN_POWER = ":POW:LOW?"  # Query min power

    # Function Selection
    FUNCTION = ":FUNC"  # Set or query function mode (VOLT, CURR, RES, POW, SHORT)

    # Measurement Commands
    MEASURE_CURRENT = ":MEAS:CURR?"  # Return the load current
    MEASURE_VOLTAGE = ":MEAS:VOLT?"  # Return the load voltage
    MEASURE_POWER = ":MEAS:POW?"  # Return the load power

    # List Mode Commands
    LIST_MODE = ":LIST"  # Output all steps in order
    RECALL_LIST = ":RCL:LIST"  # Recall/query a LIST unit

    # Overcurrent Protection (OCP)
    OCP_MODE = ":OCP"  # Output steps in OCP mode
    RECALL_OCP = ":RCL:OCP"  # Recall/query OCP settings

    # Overpower Protection (OPP)
    OPP_MODE = ":OPP"  # Output steps in OPP mode
    RECALL_OPP = ":RCL:OPP"  # Recall/query OPP settings

    # Battery Mode Commands
    BATTERY_MODE = ":BATT"  # Set battery mode
    RECALL_BATTERY = ":RCL:BATT"  # Recall/query battery mode
    BATTERY_TIME = ":BATT:TIM"  # Query battery test time
    BATTERY_CAPACITY = ":BATT:CAP"  # Query battery test capacity

    # Dynamic Mode Commands
    DYNAMIC_MODE = ":DYN"  # Query and set dynamic test mode


def test():
    print(KE103SCPICMD.SET_VOLTAGE.value)  # Output: :VOLT
    print(KE103SCPICMD.MEASURE_CURRENT.value)  # Output: :MEAS:CURR?


if __name__ == "__main__":
    test()