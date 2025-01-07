class Well:
    def __init__(self, well: str, labware_info: dict):
        self.WELL = well
        self.LOCATION = labware_info["location"]
        self.WELL_ID = f"{self.LOCATION}{self.WELL}"
        self.LABWARE_ID = labware_info["labware_id"]
        self.LABWARE_NAME = labware_info["labware_name"]
        self.MAX_VOLUME = labware_info["max_volume"]
        self.WELL_DIAMETER = labware_info["well_diameter"]
        self.volume = 0
        self.log = []

    def dispense(self, volume: float):
        """
        dispensing into the well
        """
        if self.volume + volume > self.MAX_VOLUME:
            print("Volume exceeds well capacity!")

        self.volume += volume

    def aspirate(self, volume: float):
        """
        apsirating from the well
        """
        if self.MAX_VOLUME - volume < 0:
            print("More aspirating volume than volume in well!")
        self.volume -= volume

    def measure_well():
        # TODO: implement this method
        pass

    def __str__(self):
        return f"""
        Well object
        Well: {self.WELL}
        Labware ID: {self.LABWARE_ID}
        Volume: {self.volume}
        
        """
