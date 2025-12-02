import logging

logger = logging.getLogger(__name__)

class CostCalculator:
    """
    Estimates the cost of a Databricks job run based on cluster configuration and duration.
    Uses a static DBU lookup table for common instance types.
    """

    # Static DBU Table (Simplified for MVP)
    # Source: Approximate AWS Databricks Jobs Compute pricing
    # Format: {instance_type: dbus_per_hour}
    DBU_TABLE = {
        # General Purpose
        "m5.large": 0.25,
        "m5.xlarge": 0.5,
        "m5.2xlarge": 1.0,
        "m5.4xlarge": 2.0,
        "m4.large": 0.25,
        "m4.xlarge": 0.5,
        
        # Compute Optimized
        "c5.large": 0.25,
        "c5.xlarge": 0.5,
        "c5.2xlarge": 1.0,
        "c5.4xlarge": 2.0,
        
        # Memory Optimized
        "r5.large": 0.25,
        "r5.xlarge": 0.5,
        "r5.2xlarge": 1.0,
        "r5.4xlarge": 2.0,
        
        # Storage Optimized (Delta Cache)
        "i3.xlarge": 1.0, # Often higher due to local SSD value
        "i3.2xlarge": 2.0,
        "i3.4xlarge": 4.0,
        "i3.8xlarge": 8.0,
        
        # GPU (Expensive!)
        "g4dn.xlarge": 1.0,
        "g4dn.4xlarge": 4.0,
        "p3.2xlarge": 3.0,

        # Serverless / Environment
        "Serverless": 2.0, # Estimate
    }

    # Standard List Price per DBU (Jobs Compute)
    PRICE_PER_DBU = 0.40 

    def get_dbu_for_instance(self, instance_type):
        """Returns the DBU count for a given instance type, or a default if unknown."""
        if not instance_type:
            return 0.0
        
        # Normalize type (e.g., "Standard_DS3_v2" -> "ds3_v2" mapping could be added here)
        # For now, we assume AWS-style naming or exact match
        return self.DBU_TABLE.get(instance_type, 0.5) # Default to 0.5 (small instance)

    def calculate_cost(self, cluster_spec, duration_seconds):
        """
        Calculates estimated cost for a single run.
        
        Args:
            cluster_spec (dict): The 'new_cluster' or 'existing_cluster' spec.
            duration_seconds (int): Duration of the run in seconds.
            
        Returns:
            dict: {
                "estimated_cost_usd": float,
                "total_dbus": float,
                "details": str
            }
        """
        if not cluster_spec or duration_seconds is None:
            return {"estimated_cost_usd": 0.0, "total_dbus_per_hour": 0.0, "details": "Insufficient data"}

        # 1. Identify Driver and Worker types
        driver_type = cluster_spec.get("driver_node_type_id", cluster_spec.get("node_type_id"))
        worker_type = cluster_spec.get("node_type_id")
        
        # 2. Identify Worker Count
        # Autoscale?
        autoscale = cluster_spec.get("autoscale")
        if autoscale:
            # For estimation, we take the average of min and max, or just max for conservative estimate
            min_workers = autoscale.get("min_workers", 1)
            max_workers = autoscale.get("max_workers", 1)
            num_workers = (min_workers + max_workers) / 2
            worker_count_desc = f"~{num_workers} (Autoscaling {min_workers}-{max_workers})"
        else:
            num_workers = cluster_spec.get("num_workers", 0)
            worker_count_desc = str(num_workers)

        # 3. Calculate DBUs per hour
        driver_dbu = self.get_dbu_for_instance(driver_type)
        worker_dbu = self.get_dbu_for_instance(worker_type)
        
        total_dbus_per_hour = driver_dbu + (worker_dbu * num_workers)
        
        # 4. Calculate Cost
        duration_hours = duration_seconds / 3600.0
        total_dbus_consumed = total_dbus_per_hour * duration_hours
        estimated_cost = total_dbus_consumed * self.PRICE_PER_DBU

        return {
            "estimated_cost_usd": round(estimated_cost, 4),
            "total_dbus_per_hour": total_dbus_per_hour,
            "duration_hours": round(duration_hours, 4),
            "details": f"Driver: {driver_type} ({driver_dbu} DBU) + Workers: {worker_count_desc} x {worker_type} ({worker_dbu} DBU) = {total_dbus_per_hour} DBUs/hr"
        }
