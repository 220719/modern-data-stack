with casos as (
    select * from {{ ref('stg_casos') }}
),

clima as (
    select * from {{ ref('stg_clima_semanal') }}
),

joined as (
    select
        c.municipio,
        c.geocodigo,
        c.doenca,
        c.ano,
        c.semana,
        c.data_inicio_se,
        c.semana_epidemiologica,
        c.casos_estimados,
        c.casos_confirmados,
        c.nivel_alerta,

        -- Clima da mesma semana
        cl.temp_max_media,
        cl.temp_min_media,
        cl.temp_media_semanal,
        cl.precipitacao_total,
        cl.umidade_media_semanal,

        -- Lags de casos (semanas anteriores)
        lag(c.casos_estimados, 1) over (
            partition by c.municipio, c.doenca
            order by c.semana_epidemiologica
        ) as casos_lag1,

        lag(c.casos_estimados, 2) over (
            partition by c.municipio, c.doenca
            order by c.semana_epidemiologica
        ) as casos_lag2,

        lag(c.casos_estimados, 4) over (
            partition by c.municipio, c.doenca
            order by c.semana_epidemiologica
        ) as casos_lag4,

        -- Lags de clima (semanas anteriores)
        lag(cl.temp_min_media, 2) over (
            partition by c.municipio, c.doenca
            order by c.semana_epidemiologica
        ) as temp_min_lag2,

        lag(cl.precipitacao_total, 2) over (
            partition by c.municipio, c.doenca
            order by c.semana_epidemiologica
        ) as precipitacao_lag2,

        lag(cl.umidade_media_semanal, 4) over (
            partition by c.municipio, c.doenca
            order by c.semana_epidemiologica
        ) as umidade_lag4,

        -- Média móvel 4 semanas
        avg(c.casos_estimados) over (
            partition by c.municipio, c.doenca
            order by c.semana_epidemiologica
            rows between 3 preceding and current row
        ) as media_movel_4s

    from casos c
    left join clima cl
        on c.municipio = cl.municipio
        and c.ano      = cl.ano
        and c.semana   = cl.semana
)

select * from joined
where casos_lag1 is not null