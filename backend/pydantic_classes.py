from datetime import datetime, date, time
from typing import Any, List, Optional, Union, Set
from enum import Enum
from pydantic import BaseModel, field_validator

from abc import ABC, abstractmethod

############################################
# Enumerations are defined here
############################################

class LicensingType(Enum):
    Proprietary = "Proprietary"
    Open_Source = "Open_Source"

class DatasetType(Enum):
    Test = "Test"
    Training = "Training"
    Validation = "Validation"

class ProjectStatus(Enum):
    Pending = "Pending"
    Ready = "Ready"
    Archived = "Archived"
    Created = "Created"
    Closed = "Closed"

class EvaluationStatus(Enum):
    Custom = "Custom"
    Archived = "Archived"
    Pending = "Pending"
    Done = "Done"
    Processing = "Processing"

############################################
# Classes are defined here
############################################
class EvaluationCreate(BaseModel):
    status: EvaluationStatus
    ref: List[int]  # N:M Relationship
    config: int  # N:1 Relationship (mandatory)
    evaluates: List[int]  # N:M Relationship
    observations: Optional[List[int]] = None  # 1:N Relationship
    project: int  # N:1 Relationship (mandatory)


class MeasureCreate(BaseModel):
    error: str
    unit: str
    uncertainty: float
    value: str
    measurand: int  # N:1 Relationship (mandatory)
    metric: int  # N:1 Relationship (mandatory)
    observation: int  # N:1 Relationship (mandatory)


class LegalRequirementCreate(BaseModel):
    principle: str
    legal_ref: str
    standard: str
    project_1: int  # N:1 Relationship (mandatory)


class AssessmentElementCreate(ABC, BaseModel):
    description: str
    name: str


class ObservationCreate(AssessmentElementCreate):
    observer: str
    whenObserved: datetime
    dataset: int  # N:1 Relationship (mandatory)
    measures: Optional[List[int]] = None  # 1:N Relationship
    eval: int  # N:1 Relationship (mandatory)
    tool: int  # N:1 Relationship (mandatory)


class ElementCreate(AssessmentElementCreate):
    measure: Optional[List[int]] = None  # 1:N Relationship
    project: Optional[int] = None  # N:1 Relationship (optional)
    evalu: List[int]  # N:M Relationship
    eval: List[int]  # N:M Relationship


class ToolCreate(BaseModel):
    version: str
    licensing: LicensingType
    source: str
    name: str
    observation_1: Optional[List[int]] = None  # 1:N Relationship


class MetricCreate(AssessmentElementCreate):
    measures: Optional[List[int]] = None  # 1:N Relationship
    derivedBy: List[int]  # N:M Relationship
    category: List[int]  # N:M Relationship


class DirectCreate(MetricCreate):
    pass


class ConfParamCreate(AssessmentElementCreate):
    param_type: str
    value: str
    conf: int  # N:1 Relationship (mandatory)


class MetricCategoryCreate(AssessmentElementCreate):
    metrics: List[int]  # N:M Relationship


class ConfigurationCreate(AssessmentElementCreate):
    params: Optional[List[int]] = None  # 1:N Relationship
    eval: Optional[List[int]] = None  # 1:N Relationship


class FeatureCreate(ElementCreate):
    min_value: float
    feature_type: str
    max_value: float
    features: int  # N:1 Relationship (mandatory)
    date: int  # N:1 Relationship (mandatory)


class DatashapeCreate(BaseModel):
    accepted_target_values: str
    f_features: Optional[List[int]] = None  # 1:N Relationship
    f_date: Optional[List[int]] = None  # 1:N Relationship
    dataset_1: Optional[List[int]] = None  # 1:N Relationship


class DatasetCreate(ElementCreate):
    version: str
    source: str
    dataset_type: DatasetType
    licensing: LicensingType
    observation_2: Optional[List[int]] = None  # 1:N Relationship
    datashape: int  # N:1 Relationship (mandatory)
    models: List[int]  # N:M Relationship


class ProjectCreate(BaseModel):
    name: str
    status: ProjectStatus
    legal_requirements: Optional[List[int]] = None  # 1:N Relationship
    eval: Optional[List[int]] = None  # 1:N Relationship
    involves: Optional[List[int]] = None  # 1:N Relationship


class ModelCreate(ElementCreate):
    licensing: LicensingType
    source: str
    data: str
    pid: str
    dataset: List[int]  # N:M Relationship


class DerivedCreate(MetricCreate):
    expression: str
    baseMetric: List[int]  # N:M Relationship


