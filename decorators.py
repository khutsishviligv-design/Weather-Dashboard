from functools import wraps

def validate_city(func):

    @wraps(func)
    def wrapper(city):

        if not city.replace(" ", "").isalpha():
            raise ValueError(
                "Please enter a valid city name!"
            )

        return func(city)

    return wrapper
