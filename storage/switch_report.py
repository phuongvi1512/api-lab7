from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime


class SwitchReport(Base):
    """ Switch Report """

    __tablename__ = "switch_report"

    id = Column(Integer, primary_key=True)
    trace_id = Column(String(250), nullable=False)
    report_id = Column(String(250), nullable=False)
    switch_id = Column(String(250), nullable=False)
    timestamp = Column(String(100), nullable=False)
    status = Column(String(100), nullable=False)
    temperature = Column(Integer, nullable=False)
    date_created = Column(DateTime, nullable=False)

    def __init__(self, trace_id, report_id, switch_id, timestamp, temperature, status): 
        """ Initializes a switch report """
        self.trace_id = trace_id
        self.report_id = report_id
        self.switch_id = switch_id
        self.timestamp = timestamp
        self.date_created = datetime.datetime.now() # Sets the date/time record is created
        self.status = status
        self.temperature = temperature

    def to_dict(self):
        """ Dictionary Representation of a blood pressure reading """
        dict = {}
        dict['id'] = self.id
        dict['trace_id'] = self.trace_id
        dict['report_id'] = self.report_id
        dict['switch_id'] = self.switch_id
        dict['status'] = self.status
        dict['temperature'] = self.temperature
        dict['timestamp'] = self.timestamp
        dict['date_created'] = self.date_created

        return dict
