with source as (
    select
        municipio,
        geocodigo,
        doenca,
        epoch_ms(cast(data_iniSE as bigint))::date    as data_inicio_se,
        SE                                             as semana_epidemiologica,
        cast(SE / 100 as integer)                      as ano,
        SE - cast(SE / 100 as integer) * 100           as semana,
        coalesce(casos_est, 0)                         as casos_estimados,
        coalesce(casos, 0)                             as casos_confirmados,
        coalesce(nivel, 1)                             as nivel_alerta
    from casos_raw
    where casos_est is not null
)

select * from source