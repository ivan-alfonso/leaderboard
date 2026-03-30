import enum
from typing import List, Optional
from sqlalchemy import (
    create_engine, Column, ForeignKey, Table, Text, Boolean, String, Date, 
    Time, DateTime, Float, Integer, Enum
)
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import (
    column_property, DeclarativeBase, Mapped, mapped_column, relationship
)
from datetime import datetime as dt_datetime, time as dt_time, date as dt_date

class Base(DeclarativeBase):
    pass

# Definitions of Enumerations
class LicensingType(enum.Enum):
    Open_Source = "Open_Source"
    Proprietary = "Proprietary"

class DatasetType(enum.Enum):
    Training = "Training"
    Test = "Test"
    Validation = "Validation"

class EvaluationStatus(enum.Enum):
    Processing = "Processing"
    Archived = "Archived"
    Pending = "Pending"
    Done = "Done"
    Custom = "Custom"

class ProjectStatus(enum.Enum):
    Ready = "Ready"
    Closed = "Closed"
    Created = "Created"
    Archived = "Archived"
    Pending = "Pending"


# Tables definition for many-to-many relationships
evaluation_element = Table(
    "evaluation_element",
    Base.metadata,
    Column("eval", ForeignKey("evaluation.id"), primary_key=True),
    Column("ref", ForeignKey("element.id"), primary_key=True),
)
metriccategory_metric = Table(
    "metriccategory_metric",
    Base.metadata,
    Column("metrics", ForeignKey("metric.id"), primary_key=True),
    Column("category", ForeignKey("metriccategory.id"), primary_key=True),
)
derived_metric = Table(
    "derived_metric",
    Base.metadata,
    Column("baseMetric", ForeignKey("metric.id"), primary_key=True),
    Column("derivedBy", ForeignKey("derived.id"), primary_key=True),
)
evaluates_eval = Table(
    "evaluates_eval",
    Base.metadata,
    Column("evaluates", ForeignKey("element.id"), primary_key=True),
    Column("evalu", ForeignKey("evaluation.id"), primary_key=True),
)

# Tables definition
class Project(Base):
    __tablename__ = "project"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus))

class Evaluation(Base):
    __tablename__ = "evaluation"
    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[EvaluationStatus] = mapped_column(Enum(EvaluationStatus))
    config_id: Mapped[int] = mapped_column(ForeignKey("configuration.id"))
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"))

class Measure(Base):
    __tablename__ = "measure"
    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[float] = mapped_column(Float)
    error: Mapped[str] = mapped_column(String(100))
    uncertainty: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(100))
    measurand_id: Mapped[int] = mapped_column(ForeignKey("element.id"))
    metric_id: Mapped[int] = mapped_column(ForeignKey("metric.id"))
    observation_id: Mapped[int] = mapped_column(ForeignKey("observation.id"))

class AssessmentElement(AbstractConcreteBase, Base):
    strict_attrs = True
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(100))

class Observation(AssessmentElement):
    __tablename__ = "observation"
    id: Mapped[int] = mapped_column(primary_key=True)
    observer: Mapped[str] = mapped_column(String(100))
    whenObserved: Mapped[dt_datetime] = mapped_column(DateTime)
    tool_id: Mapped[int] = mapped_column(ForeignKey("tool.id"))
    dataset_id: Mapped[int] = mapped_column(ForeignKey("dataset.id"))
    eval_id: Mapped[int] = mapped_column(ForeignKey("evaluation.id"))
    __mapper_args__ = {
        "polymorphic_identity": "observation",
        "concrete": True,
    }

class Element(AssessmentElement):
    __tablename__ = "element"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id"), nullable=True)
    type_spec: Mapped[str] = mapped_column(String(50))
    __mapper_args__ = {
        "polymorphic_identity": "element",
        "polymorphic_on": "type_spec",
    }

class Model(Element):
    __tablename__ = "model"
    id: Mapped[int] = mapped_column(ForeignKey("element.id"), primary_key=True)
    pid: Mapped[str] = mapped_column(String(100))
    data: Mapped[str] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(100))
    licensing: Mapped[LicensingType] = mapped_column(Enum(LicensingType))
    dataset_id: Mapped[int] = mapped_column(ForeignKey("dataset.id"))
    __mapper_args__ = {
        "polymorphic_identity": "model",
    }

class Metric(AssessmentElement):
    __tablename__ = "metric"
    id: Mapped[int] = mapped_column(primary_key=True)
    type_spec: Mapped[str] = mapped_column(String(50))
    __mapper_args__ = {
        "polymorphic_identity": "metric",
        "polymorphic_on": "type_spec",
    }

class Direct(Metric):
    __tablename__ = "direct"
    id: Mapped[int] = mapped_column(ForeignKey("metric.id"), primary_key=True)
    __mapper_args__ = {
        "polymorphic_identity": "Direct",
    }

class Derived(Metric):
    __tablename__ = "derived"
    id: Mapped[int] = mapped_column(ForeignKey("metric.id"), primary_key=True)
    expression: Mapped[str] = mapped_column(String(100))
    __mapper_args__ = {
        "polymorphic_identity": "Derived",
    }

class MetricCategory(AssessmentElement):
    __tablename__ = "metriccategory"
    id: Mapped[int] = mapped_column(primary_key=True)
    __mapper_args__ = {
        "polymorphic_identity": "metriccategory",
        "concrete": True,
    }

class Comments(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    Name: Mapped[str] = mapped_column(String(100))
    Comments: Mapped[str] = mapped_column(String(100))
    TimeStamp: Mapped[dt_datetime] = mapped_column(DateTime)

class LegalRequirement(Base):
    __tablename__ = "legalrequirement"
    id: Mapped[int] = mapped_column(primary_key=True)
    legal_ref: Mapped[str] = mapped_column(String(100))
    standard: Mapped[str] = mapped_column(String(100))
    principle: Mapped[str] = mapped_column(String(100))
    project_1_id: Mapped[int] = mapped_column(ForeignKey("project.id"))

class Tool(Base):
    __tablename__ = "tool"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    licensing: Mapped[LicensingType] = mapped_column(Enum(LicensingType))

class ConfParam(AssessmentElement):
    __tablename__ = "confparam"
    id: Mapped[int] = mapped_column(primary_key=True)
    param_type: Mapped[str] = mapped_column(String(100))
    value: Mapped[str] = mapped_column(String(100))
    conf_id: Mapped[int] = mapped_column(ForeignKey("configuration.id"))
    __mapper_args__ = {
        "polymorphic_identity": "confparam",
        "concrete": True,
    }

class Configuration(AssessmentElement):
    __tablename__ = "configuration"
    id: Mapped[int] = mapped_column(primary_key=True)
    __mapper_args__ = {
        "polymorphic_identity": "configuration",
        "concrete": True,
    }

class Feature(Element):
    __tablename__ = "feature"
    id: Mapped[int] = mapped_column(ForeignKey("element.id"), primary_key=True)
    min_value: Mapped[float] = mapped_column(Float)
    max_value: Mapped[float] = mapped_column(Float)
    feature_type: Mapped[str] = mapped_column(String(100))
    features_id: Mapped[int] = mapped_column(ForeignKey("datashape.id"))
    date_id: Mapped[int] = mapped_column(ForeignKey("datashape.id"))
    __mapper_args__ = {
        "polymorphic_identity": "feature",
    }

class Datashape(Base):
    __tablename__ = "datashape"
    id: Mapped[int] = mapped_column(primary_key=True)
    accepted_target_values: Mapped[str] = mapped_column(String(100))

class Dataset(Element):
    __tablename__ = "dataset"
    id: Mapped[int] = mapped_column(ForeignKey("element.id"), primary_key=True)
    source: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(100))
    licensing: Mapped[LicensingType] = mapped_column(Enum(LicensingType))
    dataset_type: Mapped[DatasetType] = mapped_column(Enum(DatasetType))
    datashape_id: Mapped[int] = mapped_column(ForeignKey("datashape.id"))
    __mapper_args__ = {
        "polymorphic_identity": "dataset",
    }


#--- Relationships of the project table
Project.legal_requirements: Mapped[List["LegalRequirement"]] = relationship("LegalRequirement", back_populates="project_1", foreign_keys=[LegalRequirement.project_1_id])
Project.involves: Mapped[List["Element"]] = relationship("Element", back_populates="project", foreign_keys=[Element.project_id])
Project.eval: Mapped[List["Evaluation"]] = relationship("Evaluation", back_populates="project", foreign_keys=[Evaluation.project_id])

#--- Relationships of the evaluation table
Evaluation.observations: Mapped[List["Observation"]] = relationship("Observation", back_populates="eval", foreign_keys=[Observation.eval_id])
Evaluation.config: Mapped["Configuration"] = relationship("Configuration", back_populates="eval", foreign_keys=[Evaluation.config_id])
Evaluation.project: Mapped["Project"] = relationship("Project", back_populates="eval", foreign_keys=[Evaluation.project_id])
Evaluation.ref: Mapped[List["Element"]] = relationship("Element", secondary=evaluation_element, back_populates="eval")
Evaluation.evaluates: Mapped[List["Element"]] = relationship("Element", secondary=evaluates_eval, back_populates="evalu")

#--- Relationships of the measure table
Measure.measurand: Mapped["Element"] = relationship("Element", back_populates="measure", foreign_keys=[Measure.measurand_id])
Measure.metric: Mapped["Metric"] = relationship("Metric", back_populates="measures", foreign_keys=[Measure.metric_id])
Measure.observation: Mapped["Observation"] = relationship("Observation", back_populates="measures", foreign_keys=[Measure.observation_id])

#--- Relationships of the observation table
Observation.tool: Mapped["Tool"] = relationship("Tool", back_populates="observation_1", foreign_keys=[Observation.tool_id])
Observation.measures: Mapped[List["Measure"]] = relationship("Measure", back_populates="observation", foreign_keys=[Measure.observation_id])
Observation.dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="observation_2", foreign_keys=[Observation.dataset_id])
Observation.eval: Mapped["Evaluation"] = relationship("Evaluation", back_populates="observations", foreign_keys=[Observation.eval_id])

#--- Relationships of the element table
Element.measure: Mapped[List["Measure"]] = relationship("Measure", back_populates="measurand", foreign_keys=[Measure.measurand_id])
Element.evalu: Mapped[List["Evaluation"]] = relationship("Evaluation", secondary=evaluates_eval, back_populates="evaluates")
Element.project: Mapped["Project"] = relationship("Project", back_populates="involves", foreign_keys=[Element.project_id])
Element.eval: Mapped[List["Evaluation"]] = relationship("Evaluation", secondary=evaluation_element, back_populates="ref")

#--- Relationships of the model table
Model.dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="models", foreign_keys=[Model.dataset_id])

#--- Relationships of the metric table
Metric.measures: Mapped[List["Measure"]] = relationship("Measure", back_populates="metric", foreign_keys=[Measure.metric_id])
Metric.category: Mapped[List["MetricCategory"]] = relationship("MetricCategory", secondary=metriccategory_metric, back_populates="metrics")
Metric.derivedBy: Mapped[List["Derived"]] = relationship("Derived", secondary=derived_metric, back_populates="baseMetric")

#--- Relationships of the derived table
Derived.baseMetric: Mapped[List["Metric"]] = relationship("Metric", secondary=derived_metric, back_populates="derivedBy")

#--- Relationships of the metriccategory table
MetricCategory.metrics: Mapped[List["Metric"]] = relationship("Metric", secondary=metriccategory_metric, back_populates="category")

#--- Relationships of the legalrequirement table
LegalRequirement.project_1: Mapped["Project"] = relationship("Project", back_populates="legal_requirements", foreign_keys=[LegalRequirement.project_1_id])

#--- Relationships of the tool table
Tool.observation_1: Mapped[List["Observation"]] = relationship("Observation", back_populates="tool", foreign_keys=[Observation.tool_id])

#--- Relationships of the confparam table
ConfParam.conf: Mapped["Configuration"] = relationship("Configuration", back_populates="params", foreign_keys=[ConfParam.conf_id])

#--- Relationships of the configuration table
Configuration.params: Mapped[List["ConfParam"]] = relationship("ConfParam", back_populates="conf", foreign_keys=[ConfParam.conf_id])
Configuration.eval: Mapped[List["Evaluation"]] = relationship("Evaluation", back_populates="config", foreign_keys=[Evaluation.config_id])

#--- Relationships of the feature table
Feature.features: Mapped["Datashape"] = relationship("Datashape", back_populates="f_features", foreign_keys=[Feature.features_id])
Feature.date: Mapped["Datashape"] = relationship("Datashape", back_populates="f_date", foreign_keys=[Feature.date_id])

#--- Relationships of the datashape table
Datashape.f_features: Mapped[List["Feature"]] = relationship("Feature", back_populates="features", foreign_keys=[Feature.features_id])
Datashape.dataset_1: Mapped[List["Dataset"]] = relationship("Dataset", back_populates="datashape", foreign_keys=[Dataset.datashape_id])
Datashape.f_date: Mapped[List["Feature"]] = relationship("Feature", back_populates="date", foreign_keys=[Feature.date_id])

#--- Relationships of the dataset table
Dataset.models: Mapped[List["Model"]] = relationship("Model", back_populates="dataset", foreign_keys=[Model.dataset_id])
Dataset.observation_2: Mapped[List["Observation"]] = relationship("Observation", back_populates="dataset", foreign_keys=[Observation.dataset_id])
Dataset.datashape: Mapped["Datashape"] = relationship("Datashape", back_populates="dataset_1", foreign_keys=[Dataset.datashape_id])

# Database connection
DATABASE_URL = "sqlite:///ai_sandbox_PSA_13_Jan_2026.db"  # SQLite connection
engine = create_engine(DATABASE_URL, echo=True)

# Create tables in the database
Base.metadata.create_all(engine, checkfirst=True)