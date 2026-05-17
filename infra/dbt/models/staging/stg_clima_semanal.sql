with clima_diario as (
    select * from {{ ref('stg_clima') }}
),

semanal as (
    select
        municipio,
        year(data)                              as ano,
        weekofyear(data)                        as semana,
        avg(temp_max)                           as temp_max_media,
        avg(temp_min)                           as temp_min_media,
        avg(temp_media)                         as temp_media_semanal,
        sum(precipitacao)                       as precipitacao_total,
        avg(umidade_media)                      as umidade_media_semanal,
        count(*)                                as dias_com_dados
    from clima_diario
    group by municipio, year(data), weekofyear(data)
)

select * from semanal