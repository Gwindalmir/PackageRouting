class PackageCorrection:
    """A correction required for a particular package."""
    def __init__(self, package_id, time, correction):
        self.id = package_id
        self.time = time
        self.correction = correction
