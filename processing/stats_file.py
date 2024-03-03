from sqlalchemy import Column, Integer, String, DateTime
from base import Base
from datetime import datetime

class StatsFile(Base):
    __tablename__ = 'stats_file'
    id = Column(Integer, primary_key=True)
    num_reports = Column(Integer)
    num_files = Column(Integer)
    max_temp = Column(Integer)
    max_file_size = Column(Integer)
    last_updated = Column(DateTime)

    def __init__(self, num_reports, num_files, max_temp, max_file_size, last_updated):
        self.num_reports = num_reports
        self.num_files = num_files
        self.max_temp = max_temp
        self.max_file_size = max_file_size
        self.last_updated = last_updated

    def to_dict(self):
        return {"id": self.id,
                "num_reports": self.num_reports, 
                "num_files": self.num_files, 
                "max_temp": self.max_temp, 
                "max_file_size": self.max_file_size,
                "last_updated": self.last_updated.strftime('%Y-%m-%d %H:%M:%S.%f')}