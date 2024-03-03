from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime


class ConfigurationFile(Base):

    __tablename__ = "configuration_file"

    id = Column(Integer, primary_key=True)
    trace_id = Column(String(250), nullable=False)
    file_id = Column(String(250), nullable=False)
    switch_id = Column(String(250), nullable=False)
    timestamp = Column(String(100), nullable=False)
    date_created = Column(DateTime, nullable=False)
    file_size = Column(Integer, nullable=False)

    def __init__(self, file_id, trace_id, switch_id, timestamp, file_size):
        """  """
        self.file_id = file_id
        self.trace_id = trace_id
        self.switch_id = switch_id
        self.timestamp = timestamp
        self.date_created = datetime.datetime.now() # Sets the date/time record is created
        self.file_size = file_size

    def to_dict(self):
        """ Dictionary Representation of a heart rate reading """
        dict = {}
        dict['id'] = self.id
        dict['trace_id'] = self.trace_id
        dict['file_id'] = self.file_id
        dict['switch_id'] = self.switch_id
        dict['file_size'] = self.file_size
        dict['timestamp'] = self.timestamp
        dict['date_created'] = self.date_created

        return dict
