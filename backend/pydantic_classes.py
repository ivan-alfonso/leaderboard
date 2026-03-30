from datetime import datetime, date, time
from typing import Any, List, Optional, Union, Set
from enum import Enum
from pydantic import BaseModel, field_validator

from abc import ABC, abstractmethod

############################################
# Enumerations are defined here
############################################

class EvaluationStatus(Enum):
    Processing = "Processing"
    Pending = "Pending"
    Archived = "Archived"
    Done = "Done"
    Custom = "Custom"

class DatasetType(Enum):
    Test = "Test"
    Training = "Training"
    Validation = "Validation"

class ProjectStatus(Enum):
    Ready = "Ready"
    Closed = "Closed"
    Created = "Created"
    Pending = "Pending"
    Archived = "Archived"

class LicensingType(Enum):
    Open_Source = "Open_Source"
    Proprietary = "Proprietary"

############################################
# Classes are defined here
############################################
class DatashapeCreate(BaseModel):
    accepted_target_values: str
    dataset_1: Optional[List[int]] = None  # 1:N Relationship
    f_date: Optional[List[int]] = None  # 1:N Relationship
    f_features: Optional[List[int]] = None  # 1:N Relationship


class ProjectCreate(BaseModel):
    name: str
    status: ProjectStatus
    legal_requirements: Optional[List[int]] = None  # 1:N Relationship
    involves: Optional[List[int]] = None  # 1:N Relationship
    eval: Optional[List[int]] = None  # 1:N Relationship


class EvaluationCreate(BaseModel):
    status: EvaluationStatus
    observations: Optional[List[int]] = None  # 1:N Relationship
    config: int  # N:1 Relationship (mandatory)
    ref: List[int]  # N:M Relationship
    evaluates: List[int]  # N:M Relationship
    project: int  # N:1 Relationship (mandatory)


class MeasureCreate(BaseModel):
    uncertainty: float
    error: str
    unit: str
    value: str
    observation: int  # N:1 Relationship (mandatory)
    metric: int  # N:1 Relationship (mandatory)
    measurand: int  # N:1 Relationship (mandatory)


class LegalRequirementCreate(BaseModel):
    legal_ref: str
    principle: str
    standard: str
    project_1: int  # N:1 Relationship (mandatory)


class AssessmentElementCreate(ABC, BaseModel):
    name: str
    description: str


class ConfigurationCreate(AssessmentElementCreate):
    eval: Optional[List[int]] = None  # 1:N Relationship
    params: Optional[List[int]] = None  # 1:N Relationship


class ObservationCreate(AssessmentElementCreate):
    whenObserved: datetime
    observer: str
    measures: Optional[List[int]] = None  # 1:N Relationship
    dataset: int  # N:1 Relationship (mandatory)
    eval: int  # N:1 Relationship (mandatory)
    tool: int  # N:1 Relationship (mandatory)


class ElementCreate(AssessmentElementCreate):
    project: Optional[int] = None  # N:1 Relationship (optional)
    eval: List[int]  # N:M Relationship
    evalu: List[int]  # N:M Relationship
    measure: Optional[List[int]] = None  # 1:N Relationship


class FeatureCreate(ElementCreate):
    min_value: float
    max_value: float
    feature_type: str
    date: int  # N:1 Relationship (mandatory)
    features: int  # N:1 Relationship (mandatory)


class DatasetCreate(ElementCreate):
    licensing: LicensingType
    version: str
    source: str
    dataset_type: DatasetType
    datashape: int  # N:1 Relationship (mandatory)
    models: List[int]  # N:M Relationship
    observation_2: Optional[List[int]] = None  # 1:N Relationship


class ModelCreate(ElementCreate):
    data: str
    pid: str
    licensing: LicensingType
    source: str
    dataset: List[int]  # N:M Relationship


class MetricCreate(AssessmentElementCreate):
    measures: Optional[List[int]] = None  # 1:N Relationship
    category: List[int]  # N:M Relationship
    derivedBy: List[int]  # N:M Relationship


class DirectCreate(MetricCreate):
    pass


class DerivedCreate(MetricCreate):
    expression: str
    baseMetric: List[int]  # N:M Relationship


class ToolCreate(BaseModel):
    name: str
    source: str
    licensing: LicensingType
    version: str
    observation_1: Optional[List[int]] = None  # 1:N Relationship


class MetricCategoryCreate(AssessmentElementCreate):
    metrics: List[int]  # N:M Relationship


class ConfParamCreate(AssessmentElementCreate):
    value: str
    param_type: str
    conf: int  # N:1 Relationship (mandatory)


