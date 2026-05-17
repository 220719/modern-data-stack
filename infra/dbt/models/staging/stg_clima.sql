with source as (
    select
        municipio,
        data::date                                          as data,
        coalesce(temperature_2m_max, 0)                    as temp_max,
        coalesce(temperature_2m_min, 0)                    as temp_min,
        coalesce(temperature_2m_mean, 0)                   as temp_media,
        coalesce(precipitation_sum, 0)                     as precipitacao,
        coalesce(relative_humidity_2m_max, 0)              as umidade_max,
        coalesce(relative_humidity_2m_min, 0)              as umidade_min,
        (coalesce(relative_humidity_2m_max, 0) +
         coalesce(relative_humidity_2m_min, 0)) / 2.0      as umidade_media
    from clima_raw
)

select * from source