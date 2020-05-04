
from Stonks.utilities import script_context
from Stonks.utilities import utility_class
import importlib
importlib.reload(utility_class)

if __name__ == "__main__":
    utility_instance = utility_class.UtilityClass()
    utility_instance.login()
    utility_instance.test_order()