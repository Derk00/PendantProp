def get_well_id(containers: dict, solution: str) -> str:
    for key, container in containers.items():
        if "tube" in container.CONTAINER_TYPE:
            if container.solution_name == solution:
                return container.WELL_ID
    raise ValueError(
        f"No container with type 'tube' and solution name '{solution}' found."
    )
